import json
import requests

# sample get
        # {
        #     "coord": {
        #         "lon": 130.4,
        #         "lat": 33.58
        #     },
        #     "weather": [
        #         {
        #             "id": 803,
        #             "main": "Clouds",
        #             "description": "broken clouds",
        #             "icon": "04d"
        #         }
        #     ],
        #     "base": "stations",
        #     "main": {
        #         "temp": 30.88,
        #         "pressure": 1012,
        #         "humidity": 66,
        #         "temp_min": 23.89,
        #         "temp_max": 36.67
        #     },
        #     "visibility": 10000,
        #     "wind": {
        #         "speed": 5.1,
        #         "deg": 320
        #     },
        #     "clouds": {
        #         "all": 75
        #     },
        #     "dt": 1567575312,
        #     "sys": {
        #         "type": 1,
        #         "id": 7998,
        #         "message": 0.0094,
        #         "country": "JP",
        #         "sunrise": 1567544041,
        #         "sunset": 1567590107
        #     },
        #     "timezone": 32400,
        #     "id": 1850418,
        #     "name": "Tenjinchō",
        #     "cod": 200
        # }

class Weather_api_data(object):
    def __init__(self):
        self.API_KEY = "21ec29a9917727f99bbe7dd28fd0c2fb"
        # wheather と forecast がある
        self.BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
        # 天神のid
        self.location_id = "1850418"
        self.weather_data_json = None

    def get_weather_data(self):
        self.weather_data_json = requests.get("{0}?id={1}&units=metric&appid={2}".format(self.BASE_URL, self.location_id, self.API_KEY)).json()

    def read_temperature(self):
        return self.weather_data_json["main"]["temp"]

    def read_pressure(self):
        return self.weather_data_json["main"]["pressure"]

    def read_humidity(self):
        return self.weather_data_json["main"]["humidity"]
    
    def read_main_data(self):
        return self.weather_data_json["main"]

    def read_weather_data(self):
        return self.weather_data_json["weather"]

        
if __name__ == '__main__':
    weather_data = Weather_api_data()
    weather_data.get_weather_data()
    print(weather_data.read_temperature())



