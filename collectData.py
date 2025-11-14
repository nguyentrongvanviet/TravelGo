import requests
import json  

KEY =  "2694e53c5bc04f29a02d7793e65f0fe3"
url = "https://api.geoapify.com/v2/places?categories=commercial&filter=circle:106.63736918846371,10.835397299075325,5000&bias=proximity:106.63736918846371,10.835397299075325&limit=20&apiKey=YOUR_API_KEY"


class DataCollector : 

    def __init__(self,APIKey) :  
        self.APIKey = APIKey  
    def URL_placesAPI(self,categories,lat,lng,radius,limit) :  
        return f"https://api.geoapify.com/v2/places?categories={categories}&filter=circle:{lng},{lat},{radius}&bias=proximity:{lng},{lat}&limit={limit}&apiKey={self.APIKey}"
    def placesAPI(self,categories,lat,lng,radius,limit,file) :  
        response = requests.get(self.URL_placesAPI(categories,lat,lng,radius,limit))
        data = response.json()
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)  



datacollector = DataCollector(KEY)
categories = ["commercial","restaurant","tourism","entertainment","healthcare","education","catering"]

for category in categories :
    datacollector.placesAPI(category,10.835397299075325,106.63736918846371,5000,100,f"{category}.json")

