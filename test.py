import requests
from datetime import datetime
KEY =  "2694e53c5bc04f29a02d7793e65f0fe3"
url = f"https://api.geoapify.com/v2/places?categories=catering&filter=circle:106.68169483128824,10.7625844,5000&bias=proximity:106.68169483128824,10.7625844&limit=1&apiKey={KEY}"
          
response = requests.get(url)
# print(response.json())

print(f"Response time: {response.elapsed.total_seconds():.4f} seconds")
print("Completed at:", datetime.now().isoformat())