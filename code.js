// The API Key provided is restricted to JSFiddle website
// Get your own API Key on https://myprojects.geoapify.com
var myAPIKey = "2694e53c5bc04f29a02d7793e65f0fe3";
var myHeaders = new Headers();
myHeaders.append("Content-Type", "application/json");

// Helper: fetch with timeout and retries (uses AbortController)
async function fetchWithTimeoutRetry(url, options = {}, { timeout = 15000, retries = 2, retryDelay = 1000 } = {}) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
      const res = await fetch(url, { ...options, signal: controller.signal });
      clearTimeout(id);
      return res;
    } catch (err) {
      clearTimeout(id);
      const isLast = attempt === retries;
      // If aborted due to timeout or connect error, retry
      if (isLast) throw err;
      // wait before retrying
      await new Promise(r => setTimeout(r, retryDelay * Math.pow(2, attempt)));
    }
  }
}

// Fallback: call public OSRM table API (no API key). Returns array of distances in meters or null.
async function callOSRMMatrix(chosen) {
  if (!Array.isArray(chosen) || chosen.length === 0) return null;
  const coords = chosen.map(f => `${f.geometry.coordinates[0]},${f.geometry.coordinates[1]}`).join(';');
  const url = `https://router.project-osrm.org/table/v1/driving/${coords}?annotations=distance`;
  try {
    const res = await fetchWithTimeoutRetry(url, { method: 'GET' }, { timeout: 15000, retries: 1 });
    if (!res.ok) throw new Error('OSRM table request failed: ' + res.status);
    const data = await res.json();
    return data.distances || null;
  } catch (err) {
    console.error('OSRM fallback failed:', err);
    return null;
  }
}

// Build a routematrix request from the local `entertainment.json` and send to Geoapify
async function buildAndSendMatrix({ limit = Infinity } = {}) {
  let features = [];
  // Try to load the local JSON (works in Node); if unavailable, attempt fetch (works in browser when served over HTTP)
  try {
    // Node environment: use fs if available
    if (typeof require === 'function') {
      const fs = require('fs');
      const file = fs.readFileSync(require('path').join(__dirname, 'entertainment.json'), 'utf8');
      const data = JSON.parse(file);
      features = data.features || [];
    }
  } catch (err) {
    // fall back to fetch (browser or Node with fetch)
    try {
      const res = await fetch('entertainment.json');
      if (!res.ok) throw new Error('Fetch failed: ' + res.status);
      const data = await res.json();
      features = data.features || [];
    } catch (err2) {
      console.error('Could not load entertainment.json via fs or fetch:', err, err2);
      return;
    }
  }

  if (!features.length) {
    console.warn('No features found in entertainment.json');
    return;
  }

  // Limit number of locations to avoid huge matrix requests
  const chosen = features.slice(0, Math.max(1, Math.min(limit, features.length)));

  // Build Geoapify routematrix structure: sources and targets (use same list for full matrix)
  const coordsToLocation = (coords) => ({ location: [coords[0], coords[1]] }); // [lon, lat]
  const body = {
    mode: 'drive',
    sources: chosen.map(f => coordsToLocation(f.geometry.coordinates)),
    targets: chosen.map(f => coordsToLocation(f.geometry.coordinates))
  };

  const requestOptions = {
    method: 'POST',
    headers: myHeaders,
    body: JSON.stringify(body)
  };

  const url = `https://api.geoapify.com/v1/routematrix?apiKey=${myAPIKey}`;
  try {
    const res = await fetchWithTimeoutRetry(url, requestOptions, { timeout: 20000, retries: 2, retryDelay: 1500 });
    if (!res.ok) throw new Error('Geoapify routematrix request failed: ' + res.status);
    const result = await res.json();
    console.log('Geoapify routematrix result:', result);
    // Example: result.distances is a matrix of meters
    return { chosen, result };
  } catch (err) {
    console.error('Error calling Geoapify routematrix (will try OSRM fallback):', err);
    // Try OSRM fallback (public router) — may also fail but no API key required
    try {
      const osrmDistances = await callOSRMMatrix(chosen);
      if (osrmDistances) {
        console.log('OSRM fallback distances obtained');
        return { chosen, result: { distances: osrmDistances } };
      }
    } catch (err2) {
      console.error('OSRM fallback also failed:', err2);
    }
    // If both fail, return chosen so caller can at least compute haversine distances locally
    return { chosen, result: null };
  }
}

// Optionally capture console output to a JSON file when running in Node
if (typeof process !== 'undefined' && process && typeof process.on === 'function') {
  try {
    const fs = require('fs');
    const path = require('path');
    const logs = [];
    const originalLog = console.log.bind(console);
    console.log = (...args) => { originalLog(...args); logs.push(args.length === 1 ? args[0] : args); };
    const outFile = path.join(__dirname, 'console-output.json');
    function writeLogs() {
      try { fs.writeFileSync(outFile, JSON.stringify(logs, null, 2), 'utf8'); originalLog('Console output saved to', outFile); }
      catch (err) { originalLog('Error saving console output:', err); }
    }
    process.on('exit', writeLogs);
    process.on('SIGINT', () => { writeLogs(); process.exit(); });
    process.on('uncaughtException', (err) => { console.log('Uncaught exception:', err); writeLogs(); process.exit(1); });
  } catch (err) {
    // ignore setup errors
  }
}

// Helper: compute full haversine N x N matrix for chosen features
function computeHaversineMatrixForChosen(chosen) {
  const toRad = (deg) => deg * Math.PI / 180;
  const R = 6371000;
  const n = chosen.length;
  const mat = Array.from({ length: n }, () => Array(n).fill(null));
  for (let i = 0; i < n; i++) {
    const [lon1, lat1] = chosen[i].geometry.coordinates;
    for (let j = 0; j < n; j++) {
      const [lon2, lat2] = chosen[j].geometry.coordinates;
      const dLat = toRad(lat2 - lat1);
      const dLon = toRad(lon2 - lon1);
      const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
                Math.sin(dLon/2) * Math.sin(dLon/2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      mat[i][j] = Math.round(R * c);
    }
  }
  return mat;
}

// Run demo for first 30 locations: compute haversine and request Geoapify routematrix (30x30)
(async function run30Matrix() {
  try {
    const limit = 30;
    const res = await buildAndSendMatrix({ limit });
    if (!res) return;
    const { chosen, result } = res;

    // compute local haversine matrix
    const haversine = computeHaversineMatrixForChosen(chosen);

    // Geoapify routing matrix (result.distances) may be present
    const routing = (result && result.distances) ? result.distances : null;

    // Prepare output object
    const out = {
      generated_at: new Date().toISOString(),
      count: chosen.length,
      places: chosen.map(f => ({ name: f.properties && f.properties.name, place_id: f.properties && f.properties.place_id, coords: f.geometry.coordinates })),
      haversine_m: haversine,
      routing_m: routing
    };

    console.log('Computed 30x30 haversine matrix and routing matrix (routing_m may be null on error).');

    // If running in Node, save to file for inspection
    if (typeof process !== 'undefined' && process && typeof require === 'function') {
      try {
        const fs = require('fs');
        const path = require('path');
        const outFile = path.join(__dirname, 'distance-matrix-30.json');
        fs.writeFileSync(outFile, JSON.stringify(out, null, 2), 'utf8');
        console.log('Saved distance matrices to', outFile);
      } catch (err) {
        console.error('Failed to write distance-matrix-30.json:', err);
      }
    }
  } catch (err) {
    console.error('run30Matrix failed:', err);
  }
})();