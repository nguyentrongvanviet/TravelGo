import requests
import json
url = "https://api.geoapify.com/v1/routematrix?apiKey=2694e53c5bc04f29a02d7793e65f0fe3"
headers = {"Content-Type": "application/json"}
data = '{"mode":"drive","sources":[{"location":[107.5264365130547,11.110184203210778]},{"location":[107.59510196777705,10.983485481945266]},{"location":[107.7296862590365,10.926857796386557]}],"targets":[{"location":[107.5264365130547,11.110184203210778]},{"location":[107.59510196777705,10.983485481945266]},{"location":[107.7296862590365,10.926857796386557]}]}'
      
try:
    resp = requests.post(url, headers=headers, data=data)
    with open("distance-matrix-30.json", "w", encoding="utf-8") as f:
        json.dump(resp.json(), f, ensure_ascii=False, indent=4)
except requests.exceptions.HTTPError as e:
    print (e.response.text)
