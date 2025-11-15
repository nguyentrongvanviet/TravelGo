import requests
import json
import csv
import time  
import gzip  
import io    

# --- Configuration ---
YOUR_NEW_HERE_API_KEY = "nCqboK-Z11CdKfCt4vAWw6AZ1-nOM6yN7BK_RMR72dE"
YOUR_FILE_PATH = "ALL.json" 
OUTPUT_CSV_FILE = "distance_matrix_100.csv" # Changed output file
POLL_INTERVAL = 15
# --- End Configuration ---

def load_coordinates_from_file(file_path):
    # (Same as before)
    coords = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            data = json.load(f)
            for location in data.get("locations", []):
                lat = float(location["coordinates"][1])
                lng = float(location["coordinates"][0])
                coords.append({"lat": lat, "lng": lng})
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error processing file data: {e}")
        return None
    return coords

def save_matrix_to_csv(distances_list, num_destinations, output_filename):
    # (Same as before)
    print(f"\nSaving matrix to {output_filename}...")
    num_origins = len(distances_list) // num_destinations
    try:
        with open(output_filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for i in range(num_origins):
                start_index = i * num_destinations
                end_index = (i + 1) * num_destinations
                row_data = distances_list[start_index:end_index]
                writer.writerow(row_data)
        print(f"Successfully saved {num_origins}x{num_destinations} matrix to {output_filename}")
    except Exception as e:
        print(f"Error writing to CSV file: {e}")

def poll_for_result(status_url, api_key):
    # (Same as before)
    params = {"apiKey": api_key}
    while True:
        try:
            status_response = requests.get(status_url, params=params)
            status_response.raise_for_status()
            status_data = status_response.json()
            status = status_data.get('status')
            print(f"Polling... current status: {status}")

            if status == 'succeeded':
                download_url = status_data.get('resultUrl')
                print(f"Job complete! Downloading result from: {download_url}")
                result_response = requests.get(download_url, params=params) 
                result_response.raise_for_status()
                decompressed_data = gzip.decompress(result_response.content)
                final_data = json.loads(decompressed_data)
                return final_data.get('matrix') 

            elif status == 'failed':
                print(f"Error: Matrix job failed. Details: {status_data.get('error')}")
                return None
            time.sleep(POLL_INTERVAL)
        except requests.exceptions.RequestException as e:
            print(f"Error during polling: {e}")
            return None
        except Exception as e:
            print(f"Error processing final result: {e}")
            return None

def main():
    if YOUR_NEW_HERE_API_KEY == "PASTE_YOUR_NEW_HERE_API_KEY_HERE":
        print("Error: Please paste your new HERE API Key.")
        return

    # 1. Load coordinates
    print(f"Loading coordinates from {YOUR_FILE_PATH}...")
    locations = load_coordinates_from_file(YOUR_FILE_PATH)
    if not locations:
        print("No coordinates were loaded. Exiting.")
        return
    print(f"Successfully loaded {len(locations)} total locations.")

    # --- THIS IS THE TEST ---
    # Let's just use the first 100 locations for this test
    locations = locations[:100]
    # ----------------------------

    print(f"Testing with the first {len(locations)} locations...")

    # 2. Define the API request payload
    region_definition = {
        "type": "circle",
        "center": {"lat":10.761577,"lng":106.680637}, 
        "radius": 5000         
    }

    payload = {
        "origins": locations,
        "destinations": locations,
        "regionDefinition": region_definition,
        "matrixAttributes": ["distances"] 
    }

    # 3. Make the API Call
    endpoint = "https://matrix.router.hereapi.com/v8/matrix"
    params = {"apiKey": YOUR_NEW_HERE_API_KEY}

    print(f"Sending {len(locations)}x{len(locations)} matrix request to HERE API...")
    
    try:
        #
        # --- THIS IS THE FIX ---
        response = requests.post(endpoint, params=params, json=payload, timeout=120)
        # -----------------------
        #
        response.raise_for_status() 
        data = response.json()
        
        matrix_data = None
        
        if 'matrix' in data:
            print("\n--- Success (Synchronous) ---")
            matrix_data = data['matrix']
        
        elif 'statusUrl' in data:
            print("\n--- Job Accepted (Asynchronous) ---")
            print("Starting to poll...")
            status_url = data['statusUrl']
            matrix_data = poll_for_result(status_url, YOUR_NEW_HERE_API_KEY)
            
        else:
            print("Error: Unknown response format.")
            print(data)
            return

        if not matrix_data:
            print("Failed to retrieve matrix data.")
            return

        # 4. Process the response
        if 'distances' not in matrix_data:
            print("Error: 'distances' key not found in final matrix data.")
            return
            
        distances_list = matrix_data['distances']
        num_destinations = len(locations)
        print(f"Total elements (distances) received: {len(distances_list)}")

        # 5. Save the matrix to CSV
        save_matrix_to_csv(distances_list, num_destinations, OUTPUT_CSV_FILE)

    except requests.exceptions.HTTPError as e:
        print(f"\n--- HTTP Error ---")
        print(f"Status Code: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        if e.response.status_code == 401:
             print("\nTHIS IS A 401 ERROR.")
             print("This confirms your key does not have permission for region-based matrix requests.")

    except Exception as e:
        print(f"\n--- An unexpected error occurred ---")
        print(e)

if __name__ == "__main__":
    main()