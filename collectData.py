import requests
import json  

url = "https://api.geoapify.com/v2/places?categories=commercial&filter=circle:106.63736918846371,10.835397299075325,5000&bias=proximity:106.63736918846371,10.835397299075325&limit=20&apiKey=YOUR_API_KEY"

KEY =  "2694e53c5bc04f29a02d7793e65f0fe3"

class DataCollector : 
    num_of_places = 0 
    categories = ["catering","commercial","entertainment"]
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
        with open(file,'w',encoding='utf-8') as outputFile :
            content = {}
            with open("ALL.json",'r', encoding  = 'utf-8') as f  : 
                data={"mode":"drive","sources":[],"targets":[]}
                ALLdata= json.load(f)
                for location in ALLdata['locations'] :
                    content[f'{location["id"]}'] = {}
                    data['sources'].append({"location":location['coordinates']})
                    data['targets'] = [] 
                    listofid = [] 
                    for  other in ALLdata['locations'] : 
                        data['targets'].append({"location":other['coordinates']})   
                        listofid.append(other['id'])
                        if len(data['targets']) == 20 : 
                            headers = {"Content-Type": "application/json"}
                            resp = requests.post(self.URL_matrix2D(), headers=headers, data=json.dumps(data)).json()
                            i = 0 
                            for distime in resp['sources_to_targets'][0]:
                                content[f"{location['id']}"][listofid[i]] = {
                                                                                "distance" : distime['distance'],
                                                                               "time" : distime['time']
                                                                            }
                                i += 1
                            data['targets'] = []
                            listofid = [] 

                    data['sources'] = []
            json.dump(content,outputFile,indent=4,ensure_ascii=False)
                


datacollector = DataCollector(KEY)
 
for category in datacollector.categories :
    datacollector.placesAPI(category,10.835397299075325,106.63736918846371,5000,7,f"{category}.json")
datacollector.Combine("ALL.json")
datacollector.distance2DMatrix("distance-matrix-2D.json")