import boto3
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
 
def cast_timestamp_array_to_datetime(timestamp_array):
    datetime_array = []
    for timestamp in timestamp_array:
        datetime_array.append(datetime.fromtimestamp(int(timestamp)))
    return datetime_array

def cast_datetime_array_to_timestamp(datetime_array):
    timestamp_array = []
    for i in datetime_array:
        timestamp_array.append(datetime.timestamp(i))
    return timestamp_array

class CommonData(object):
    def __init__(self):
        self.container = None
        self.counter = None
        self.timestamp = None
        self.time = None

    def set_data(self, data_dict):
        self.counter = data_dict[0]
        self.container = data_dict[1:]
        self.timestamp = self._adjust_timestamp("measured_time")
        self.time = cast_timestamp_array_to_datetime(self.timestamp)
    
    def _adjust_timestamp(self, keyword):
        timestamp_arrays = []
        for i in range(len(self.container)):
            # 全部 26分0秒とか、0秒にしたいので
            now_timestamp = datetime.fromtimestamp(int(self.container[i][keyword])).replace(second=0, microsecond=0)
            timestamp_arrays.append(int(now_timestamp.timestamp()))
        return timestamp_arrays

    def _float_data_extraction(self, keyword):
        keyword_data = []
        for i in range(len(self.container)):
            keyword_data.append(round(float(self.container[i][keyword]), 1))
        return keyword_data


class SpaceData(CommonData):
    def __init__(self):
        self.temp_max = None
        self.temp_min = None
        self.outside_temp = None
        self.room_temperature = None
        self.humidity = None
        self.co2 = None
        self.pressure = None

    def set_data(self, data_dict):
        super().__init__()
        super().set_data(data_dict)
        self.temp_max = super()._float_data_extraction("temp_max")
        self.temp_min = super()._float_data_extraction("temp_min")
        self.outside_temp = super()._float_data_extraction("temp")
        self.room_temperature = super()._float_data_extraction("temperature")
        self.co2 = super()._float_data_extraction("CO2")
        self.humidity = super()._float_data_extraction("humidity")
        self.pressure = super()._float_data_extraction("pressure")


class HumanData(CommonData):
    def __init__(self):
        self.human_counter = None

    def set_data(self, data_dict):
        super().__init__()
        super().set_data(data_dict)
        self.human_counter = super()._float_data_extraction("human")


class dynamoData(object):
    raspi_1 = 'raspi_1'
    raspi_2 = 'raspi_2'
    def __init__(self, device_name):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('plute_room_data')
        self.device_name = device_name

    def _get_data(self, from_datetime, to_datetime):
        print("get data from {0} to {1}".format(from_datetime, to_datetime))

        # dynamodb にあるdatetimeは13桁版なので13桁になるように整形
        from_timestamp = int(from_datetime.timestamp() * 1000)
        to_timestamp = int(to_datetime.timestamp() * 1000)
        response = self.table.query(KeyConditionExpression=Key('device_name').eq(self.device_name) & Key('datatime').between(from_timestamp, to_timestamp))
        # header として device_nameを先頭に追加した後、dynamodbから取得したデータを連結させる
        data = [response['Count']]
        for i in range(response['Count']):
            data.append(response['Items'][i]['payloads'])
        if self.device_name == dynamoData.raspi_1:
            humanData = HumanData()
            humanData.set_data(data)
            return humanData
        elif self.device_name == dynamoData.raspi_2:
            spaceData = SpaceData()
            spaceData.set_data(data)
            return spaceData
        return None

    def get_n_days_ago_data(self, number):
        today_start = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        n_minus_one_days_ago = today_start - timedelta(days=number-1)
        n_days_ago = today_start - timedelta(days=number)
    
        return self._get_data(n_days_ago, n_minus_one_days_ago)

    def get_yesterday_data(self):
        today_start = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        yesterday = today_start - timedelta(days=1)
    
        return self._get_data(yesterday, today_start)

    def get_today_data(self):
        today_start = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        today_now = datetime.now()

        return self._get_data(today_start, today_now)
    
class MergeDynamoData(SpaceData, HumanData):
    def __init__(self):
        SpaceData.__init__(self)
        HumanData.__init__(self)
        self.raspi_1_data = dynamoData(dynamoData.raspi_1)
        self.raspi_2_data = dynamoData(dynamoData.raspi_2)
        self.this_days_datetime_array = None

    def _data_merge(self, raspi_1_day_data, raspi_2_day_data):
        self.this_days_datetime_array = self._get_this_days_datetime_array(raspi_1_day_data.time[0])
        if self.this_days_datetime_array[0] == raspi_2_day_data.time[0].replace(hour=0,minute=0,second=0,microsecond=0):
            print("this day data start from 0:00  !!")
        else:
            print("this day data don't start from 0:00")
        
        day_minutes = 24 * 60
        if len(raspi_1_day_data.timestamp) == day_minutes and len(raspi_2_day_data.timestamp) == day_minutes:
            self.temp_max = raspi_2_day_data.temp_max
            self.temp_min = raspi_2_day_data.temp_min
            self.humidity = raspi_2_day_data.humidity
            self.room_temperature = raspi_2_day_data.room_temperature
            self.outside_temp = raspi_2_day_data.outside_temp
            self.pressure = raspi_2_day_data.pressure
            self.co2 = raspi_2_day_data.co2
            self.human_counter = raspi_1_day_data.human_counter
            self.timestamp = raspi_1_day_data.timestamp
            self.time = cast_timestamp_array_to_datetime(self.timestamp)
            self.counter = len(self.timestamp)
        else:
            raspi_2_time_adjust = self._compare_time_array(raspi_2_day_data.time)
            raspi_1_time_adjust = self._compare_time_array(raspi_1_day_data.time)
            self.time = self.this_days_datetime_array
            self.temp_max = self._data_adjust(raspi_2_day_data.temp_max, raspi_2_time_adjust)
            self.temp_min = self._data_adjust(raspi_2_day_data.temp_min, raspi_2_time_adjust)
            self.humidity = self._data_adjust(raspi_2_day_data.humidity, raspi_2_time_adjust)
            self.room_temperature = self._data_adjust(raspi_2_day_data.room_temperature, raspi_2_time_adjust)
            self.outside_temp = self._data_adjust(raspi_2_day_data.outside_temp, raspi_2_time_adjust)
            self.pressure = self._data_adjust(raspi_2_day_data.pressure, raspi_2_time_adjust)
            self.co2 = self._data_adjust(raspi_2_day_data.co2, raspi_2_time_adjust)
            self.human_counter = self._data_adjust(raspi_1_day_data.human_counter, raspi_1_time_adjust)
            self.timestamp = cast_datetime_array_to_timestamp(self.time)
            self.counter = len(self.timestamp)
            # print(len(self.human_counter))
            # count = 0
            # for i in raspi_1_time_adjust:
            #     if i is True:
            #         count += 1
            # print(count)
            # print(len(raspi_1_day_data.time))

        return self

    def _data_adjust(self, data_array, time_array):
        new_data_array = []
        counter = 0
        for flg in time_array:
            if flg is True:
                new_data_array.append(data_array[counter])
                counter += 1
            else:
                new_data_array.append(None)
        return new_data_array
        
    def _compare_time_array(self, data_time_array):
        new_data_time_array = []
        j = 0
        for i in range(len(data_time_array)):
            # print("{0}  {1}  {2}".format(self.this_days_datetime_array[i+j], data_time_array[i], self.this_days_datetime_array[i+j] == data_time_array[i]))
            if self.this_days_datetime_array[i + j] == data_time_array[i]:
                new_data_time_array.append(True)
            else:
                # print(" ------- error raised -------")
                for k in range(i + j + 1, len(self.this_days_datetime_array)):
                    new_data_time_array.append(False)
                    # print("{0}  {1}  {2}".format(self.this_days_datetime_array[k] ,data_time_array[i], self.this_days_datetime_array[k] == data_time_array[i]))
                    if self.this_days_datetime_array[k] == data_time_array[i]:
                        j = k - i
                        new_data_time_array.append(True)
                        break
        for i in range(len(self.this_days_datetime_array) - len(new_data_time_array)):
            new_data_time_array.append(False)
        return new_data_time_array


    def _get_this_days_datetime_array(self, this_day_time):
        start_datetime = this_day_time.replace(hour=0,minute=0,second=0,microsecond=0)
        day_minutes = 24 * 60
        this_days_datetime_array = []
        for i in range(day_minutes):
            this_days_datetime_array.append(start_datetime + timedelta(minutes=i))
        return this_days_datetime_array

    def get_n_days_ago_data(self, number):
        raspi_1_data = self.raspi_1_data.get_n_days_ago_data(number)
        raspi_2_data = self.raspi_2_data.get_n_days_ago_data(number)
        return self._data_merge(raspi_1_data, raspi_2_data)
            
    def get_yesterday_data(self):
        raspi_1_data = self.raspi_1_data.get_yesterday_data()
        raspi_2_data = self.raspi_2_data.get_yesterday_data()
        return self._data_merge(raspi_1_data, raspi_2_data)

    def get_today_data(self):
        raspi_1_data = self.raspi_1_data.get_today_data()
        raspi_2_data = self.raspi_2_data.get_today_data()
        return self._data_merge(raspi_1_data, raspi_2_data)
                

if __name__ == "__main__":

    # --- raspi 1 はまだ未実装 ----
    raspi_1_data = dynamoData('raspi_1')
    today_raspi_1_data = raspi_1_data.get_today_data()
    # print(today_raspi_1_data.human_counter)

    # yesterday_raspi_1_data = raspi_1_data.get_n_days_ago_data(1)
    # print(yesterday_raspi_1_data.time)
    # print(len(today_raspi_1_data.human_counter))

    # raspi_2_data = dynamoData(dynamoData.raspi_2)
    # yesterday_data = raspi_2_data.get_yesterday_data()
    # print(yesterday_data.time)
    # raspi_2_data = dynamoData(dynamoData.raspi_2)
    # two_days_ago_data = raspi_2_data.get_n_days_ago_data(4)
    # print(two_days_ago_data.timestamp)
    mergeDynamoData = MergeDynamoData()
    a = mergeDynamoData.get_today_data()
    # print(a.temp_max)
    # print(a.temp_min)
    # print(a.room_temperature)
    # print(a.outside_temp)
    # print(a.human_counter)
    # print(a.co2)
    # print(a.pressure)
    # print(a.time)
    # print(a.timestamp)


    