import boto3
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
 
def cast_timestamp_array_to_datetime(timestamp_array):
    datetime_array = []
    for timestamp in timestamp_array:
        datetime_array.append(datetime.fromtimestamp(int(timestamp)))
    return datetime_array

class SpaceData(object):
    def __init__(self, data_dict):
        # self.container = data_dict[1:]
        self.container = data_dict
        self.temp_max = self._float_data_extraction("temp_max")
        self.temp_min = self._float_data_extraction("temp_min")
        self.outside_temp = self._float_data_extraction("temp")
        self.room_temperature = self._float_data_extraction("temperature")
        self.co2 = self._float_data_extraction("CO2")
        self.humidity = self._float_data_extraction("humidity")
        self.pressure = self._float_data_extraction("pressure")
        self.timestamp = self._float_data_extraction("measured_time")
        self.time = cast_timestamp_array_to_datetime(self.timestamp)

    def _float_data_extraction(self, keyword):
        keyword_data = []
        for i in range(len(self.container)):
            keyword_data.append(round(float(self.container[i][keyword]), 1))
        return keyword_data

class HumanData(object):
    def __init__(self, data_dict):
        self.container = data_dict
        self.human_exsist = self._float_data_extraction("human")
        self.timestamp = self._float_data_extraction("measured_time")
        self.time = cast_timestamp_array_to_datetime(self.timestamp)
    
    def _float_data_extraction(self, keyword):
        keyword_data = []
        for i in range(len(self.container)):
            keyword_data.append(round(float(self.container[i][keyword]), 1))
        return keyword_data


class dynamoData(object):
    def __init__(self, device_name):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('plute_room_data')
        self.device_name = device_name

    def _get_data(self, from_datetime, to_datetime):
        print("get data from {0} to {1}".format(from_datetime, to_datetime))
        from_timestamp = int(from_datetime.timestamp() * 1000)
        to_timestamp = int(to_datetime.timestamp() * 1000)
        response = self.table.query(KeyConditionExpression=Key('device_name').eq(self.device_name) & Key('datatime').between(from_timestamp, to_timestamp))
        # header として device_nameを先頭に追加した後、dynamodbから取得したデータを連結させる
        # data = [self.device_name]
        data = []
        for i in range(response['Count']):
            data.append(response['Items'][i]['payloads'])

        if self.device_name == 'raspi_1':
            return HumanData(data)
        elif self.device_name == 'raspi_2':
            return SpaceData(data)
        # try:
        #     if self.device_name == 'raspi_1':
        #         return HumanData(data)
        #     elif self.device_name == 'raspi_2':
        #         return SpaceData(data)
        # except:
            print("data is not exsist!! ")
        return None

    def get_yesterday_data(self):
        today_start = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        yesterday = today_start - timedelta(days=1)
    
        return self._get_data(yesterday, today_start)

    def get_today_data(self):
        today_start = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        today_now = datetime.now()

        return self._get_data(today_start, today_now)
    

if __name__ == "__main__":

    # --- raspi 1 はまだ未実装 ----
    # raspi_1_data = dynamoData('raspi_1')
    # today_raspi_1_data = raspi_1_data.get_today_data()
    # print(today_raspi_1_data.human_exsist)


    raspi_2_data = dynamoData('raspi_2')
    today_data = raspi_2_data.get_today_data()
    yesterday_data = raspi_2_data.get_yesterday_data()
    print(yesterday_data.room_temperature)

    