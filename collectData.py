import requests
import json  
import numpy as np 
url = "https://api.geoapify.com/v2/places?categories=commercial&filter=circle:106.63736918846371,10.835397299075325,5000&bias=proximity:106.63736918846371,10.835397299075325&limit=20&apiKey=YOUR_API_KEY"

KEY =  "06f5d1f823854d18b1e24b8e4ea4bdfb"

class DataCollector : 
    num_of_places = 0 
    categories = ["catering","commercial","entertainment","natural"]
    API_KEYS = [
    "06f5d1f823854d18b1e24b8e4ea4bdfb",
    "29b3210ac4c448cdb773280c32a5a7a6",
    # Add as many keys as you have
]
    def __init__(self,APIKey) :  
        self.APIKey = APIKey  
    def URL_places(self,categories,lat,lng,radius,limit) :  
        return f"https://api.geoapify.com/v2/places?categories={categories}&filter=circle:{lng},{lat},{radius}&bias=proximity:{lng},{lat}&limit={limit}&apiKey={self.APIKey}"
    def placesAPI(self,categories,lat,lng,radius,limit,file) :  
        response = requests.get(self.URL_places(categories,lat,lng,radius,limit))
        data = response.json()

        data['type'] = f"category_{categories}, radius_{radius}, limit_{limit}"
        
        for place in data['features']:
            place['id'] = self.num_of_places
            self.num_of_places += 1
        
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)  
    def Combine(self,file) :
        with open("ALL.json","w",encoding='utf-8') as file :
            content={"locations":[]}
            # extract only 'coordinate' and 'id' 
            for category in self.categories : 
                with open(category+".json",'r', encoding='utf-8')  as inputFile:
                    data = json.load(inputFile)
                    for location in data['features'] :
                        content["locations"].append({"id": location['id'], "coordinates": location['geometry']['coordinates']})
            json.dump(content,file,indent=4,ensure_ascii=False)
    def URL_matrix2D(self) : 
        return f"https://api.geoapify.com/v1/routematrix?apiKey={self.APIKey}"
    def distance2DMatrix(self,file) : 
        matrix2D = np.zeros((self.num_of_places,self.num_of_places))
        headers = {"Content-Type": "application/json"}
        with open("ALL.json",'r', encoding  = 'utf-8') as f  : 
            data={"mode":"drive","sources":[],"targets":[]}
            ALLdata= json.load(f)
            for  other in ALLdata['locations'] : 
                data['targets'].append({"location":other['coordinates']})   
            for location in ALLdata['locations'] :
                try :
                    data['sources']=[{"location":location['coordinates']}]
                    resp = requests.post(self.URL_matrix2D(), headers=headers, data=json.dumps(data)).json()
                    for i in range(len(ALLdata['locations'])) :
                        matrix2D[location['id'],i] = resp['sources_to_targets'][0][i]['distance']
                except requests.exceptions.HTTPError as e:
                    print (e.response.text)
        np.savetxt('matrix2D.csv', matrix2D, delimiter=',',fmt='%.0f')

                


datacollector = DataCollector(KEY)
 
for category in datacollector.categories :
    datacollector.placesAPI(category,10.835397299075325,106.63736918846371,5000,75,f"{category}.json")
datacollector.Combine("ALL.json")
# datacollector.distance2DMatrix("distance-matrix-2D.json")