var data = {
  "api": "/v1/geocode/reverse",
  "params": {
    "lang": "de",
    "limit": "3"
  },
  "inputs": [{
    "id": "optional-input-id1",
    "params": {
      "lat": "51.156397",
      "lon": "10.875491"
    }
  }]
};

// The API Key provided is restricted to JSFiddle website
// Get your own API Key on https://myprojects.geoapify.com
var myAPIKey = "6dc7fb95a3b246cfa0f3bcef5ce9ed9a";

var url = `https://api.geoapify.com/v1/batch?apiKey=${myAPIKey}`;

fetch(url, {
    method: 'post',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
  .then(getBodyAndStatus)
  .then((result) => {
    if (result.status !== 202) {
      return Promise.reject(result)
    } else {
      return getAsyncResult(`${url}&id=${result.body.id}`, 1000, 100).then(queryResult => {
        console.log(queryResult);
        return queryResult;
      });
    }
  })
  .catch(err => console.log(err));


function getBodyAndStatus(response) {
  return response.json().then(responceBody => {
    return {
      status: response.status,
      body: responceBody
    }
  });
}

function getAsyncResult(url, timeout, maxAttempt) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      repeatUntilSuccess(resolve, reject, 0)
    }, timeout);
  });

  function repeatUntilSuccess(resolve, reject, attempt) {
    console.log("Attempt: " + attempt);
    fetch(url)
      .then(getBodyAndStatus)
      .then(result => {
        if (result.status === 200) {
          resolve(result.body);
        } else if (attempt >= maxAttempt) {
          reject("Max amount of attempt achived");
        } else if (result.status === 202) {
          // Check again after timeout
          setTimeout(() => {
            repeatUntilSuccess(resolve, reject, attempt + 1)
          }, timeout);
        } else {
          // Something went wrong
          reject(result.body)
        }
      })
      .catch(err => reject(err));
  };
}