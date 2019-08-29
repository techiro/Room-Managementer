import requests
import json 

url = "http://funnel.soracom.io"
params = json.dumps({"temparature": "28", "humidity": "60", "illuminance": "600", "CO2": "20", "number_of_human": "3"})
response = requests.post(url, params, headers={'Content-Type': 'application/json'})
print(response)