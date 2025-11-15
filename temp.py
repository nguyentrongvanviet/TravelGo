import requests
import json
import csv
import time  
import gzip  
import io    

# --- Configuration ---
# 1. PASTE YOUR NEW API KEY HERE
# (The key you posted is exposed! Please generate a new one.)
YOUR_API_KEY = "nCqboK-Z11CdKfCt4vAWw6AZ1-nOM6yN7BK_RMR72dE"

# 2. SET YOUR FILE PATH HERE
YOUR_FILE_PATH = "ALL.json" 

# 3. SET YOUR OUTPUT FILE NAME
OUTPUT_CSV_FILE = "distance_matrix.csv"

# 4. SET POLLING INTERVAL (in seconds)
POLL_INTERVAL = 15
# --- End Configuration ---

def load_coordinates_from_file(file_path):
    """
    Loads coordinates from a JSON file.
    Assumes format: {"locations": [{"id": 0, "coordinates": [lng, lat]}, ...]}
    
    Returns a list of dictionaries: [{'lat': 52.5, 'lng': 13.4}, ...]
    """
    coords = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            data = json.load(f)
            for location in data.get("locations", []):
                # Assumes lat is index 1, lng is index 0
                lat = float(location["coordinates"][1])
                lng = float(location["coordinates"][0])
                coords.append({"lat": lat, "lng": lng})
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except (ValueError, IndexError, TypeError) as e:
        print(f"Error processing file data: {e}")
        return None
    
    return coords

def save_matrix_to_csv(distances_list, num_destinations, output_filename):
    """
    Saves the flattened distance matrix to a 2D CSV file.
    """
    print(f"\nSaving matrix to {output_filename}...")
    
    # Calculate the number of origins (should be the same as destinations)
    num_origins = len(distances_list) // num_destinations
    
    try:
        with open(output_filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            for i in range(num_origins):
                # Find the start and end of this origin's data in the flat list
                start_index = i * num_destinations
                end_index = (i + 1) * num_destinations
                
                # Get the slice of distances for the current origin 'i'
                row_data = distances_list[start_index:end_index]
                
                # Write this row to the CSV
                writer.writerow(row_data)
                
        print(f"Successfully saved {num_origins}x{num_destinations} matrix to {output_filename}")

    except IOError as e:
        print(f"Error writing to CSV file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during CSV writing: {e}")


def poll_for_result(status_url, api_key):
    """
    Polls the status URL until the job is 'succeeded' or 'failed'.
    """
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
                if not download_url:
                    print("Error: Job succeeded but no resultUrl found.")
                    return None
                    
                print(f"Job complete! Downloading result from: {download_url}")
                
                #
                # --- THIS IS THE FIX ---
                # We must pass the 'params' with the apiKey to the download URL as well.
                #
                result_response = requests.get(download_url, params=params) 
                
                result_response.raise_for_status()
                
                # The result is gzipped! We must decompress it.
                decompressed_data = gzip.decompress(result_response.content)
                final_data = json.loads(decompressed_data)
                
                # The final data *should* have the 'matrix' key
                return final_data.get('matrix') 

            elif status == 'failed':
                print(f"Error: Matrix job failed.")
                print(f"Details: {status_data.get('error')}")
                return None
            
            # If status is 'accepted' or 'processing', wait and poll again
            time.sleep(POLL_INTERVAL)

        except requests.exceptions.RequestException as e:
            print(f"Error during polling: {e}")
            return None
        except (gzip.BadGzipFile, json.JSONDecodeError) as e:
            print(f"Error processing final result: {e}")
            return None


def main():
    if YOUR_API_KEY == "PASTE_YOUR_NEW_HERE_API_KEY_HERE" or YOUR_API_KEY == "YOUR_HERE_API_KEY_GOES_HERE":
        print("Error: Please paste your new HERE API Key into the YOUR_API_KEY variable.")
        return

    # 1. Load coordinates from your file
    print(f"Loading coordinates from {YOUR_FILE_PATH}...")
    locations = load_coordinates_from_file(YOUR_FILE_PATH)
    
    if not locations:
        print("No coordinates were loaded. Exiting.")
        return

    print(f"Successfully loaded {len(locations)} locations.")

    # 2. Define the API request payload
    region_definition = {
        "type": "circle",
        "center": {"lat":10.761577,"lng":106.680637}, # Your defined center
        "radius": 5000         # 5,000 meters (5km)
    }

    payload = {
        "origins": locations,
        "destinations": locations,
        "regionDefinition": region_definition,
        "matrixAttributes": ["distances"] # Only asking for distances
    }

    # 3. Make the API Call
    endpoint = "https://matrix.router.hereapi.com/v8/matrix"
    params = {
        "apiKey": YOUR_API_KEY 
    }

    print(f"Sending {len(locations)}x{len(locations)} matrix request to HERE API...")
    
    try:
        response = requests.post(endpoint, params=params, json=payload, timeout=120) # 2-min timeout
        response.raise_for_status() 
        data = response.json()
        
        matrix_data = None
        
        # --- LOGIC TO HANDLE SYNC vs ASYNC ---
        if 'matrix' in data:
            # SYNC PATH: Request was small and completed immediately
            print("\n--- Success (Synchronous) ---")
            matrix_data = data['matrix']
        
        elif 'statusUrl' in data:
            # ASYNC PATH: Request was large and accepted for polling
            print("\n--- Job Accepted (Asynchronous) ---")
            print("This may take several minutes. Starting to poll...")
            status_url = data['statusUrl']
            matrix_data = poll_for_result(status_url, YOUR_API_KEY)
            
        else:
            print("Error: Unknown response format. Neither 'matrix' nor 'statusUrl' found.")
            print(data)
            return
        # --- END OF LOGIC ---

        if not matrix_data:
            print("Failed to retrieve matrix data.")
            return

        # 4. Process the response
        if 'distances' not in matrix_data:
            print("Error: 'distances' key not found in final matrix data.")
            print("Response:", matrix_data)
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
    except requests.exceptions.RequestException as e:
        print(f"\n--- Request Error ---")
        print(e)
    except KeyError as e:
        print(f"\n--- Data Error ---")
        print(f"Could not find key {e} in the response. Full response:")
        print(response.text)

if __name__ == "__main__":
    main()