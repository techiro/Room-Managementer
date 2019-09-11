import boto3
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator
##以下は消す
import os
import requests
import json
def cast_timestamp_array_to_datetime(timestamp_array):
    datetime_array = []
    for timestamp in timestamp_array:
        datetime_array.append(datetime.fromtimestamp(int(timestamp)))
    return datetime_array


class MakeGraph(object):
    def __init__(self, spacedata):
        self.counter = spacedata.counter
        self.outside_graph = spacedata.outside_temp
        self.inside_graph = spacedata.room_temperature
        self.co2_graph = spacedata.co2
        self.humidity_graph = spacedata.humidity
        self.time_graph = spacedata.time
        self.pressure_graph = spacedata.pressure
        self.location = 'plute-room-picture'
        self.save_dir = '/tmp/'
        self.hour = [f"{num}:00" for num in range(0,24,2)]
        self.figure_num = 0
        self.today_start = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        self.today_end = self.today_start + timedelta(days=1) - timedelta(minutes=1)
        self.now = datetime.now()
        self.xfmt = mdates.DateFormatter("%H:%M")
        self.xloc = mdates.HourLocator(byhour=range(0, 24, 2), tz=None)
    def _graph_name(self,location,label_name):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(location)
        fig_name = 'figure_{0:%m%d%H%M}_{1}'.format(self.now,label_name)
        return fig_name
    def push_s3_object(self,objectname):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(self.location)
        bucket.upload_file('/tmp/{0}.png'.format(objectname), 'gragh/{0}.png'.format(objectname))
        print(objectname)

    def _put_graph_toslack(self,filename):
        url = 'https://plute-room-picture.s3-ap-northeast-1.amazonaws.com/gragh/{0}.png'.format(filename)
        print(url)
        SLACK_POST_URL = 'https://hooks.slack.com/services/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'
        _counter = self.counter
        _counter = 0 if _counter == 0 else _counter-1
        print(_counter)
        nowtime = '{0:%m月%d日%H:%M}'.format(self.time_graph[_counter])
        nowtemparature = self.inside_graph[_counter]
        nowhumidity = self.humidity_graph[_counter]
        nowco2 = self.co2_graph[_counter]
        nowpressure = self.pressure_graph[_counter]
        content = f"plutoの最新の状態:\n時刻{nowtime}\n温度{nowtemparature}℃\n湿度:{nowhumidity}%\n気圧:{nowpressure}hPa\nCO2:{nowco2}ppm"

        post_json = {
            "text": content,
            "attachments": [{
            "fallback": filename,
            "text": filename,
            "color": "#36a64f", #// 'good'、'warning'、'danger' 、または 16 進数のカラーコードのいずれかになります
            "image_url": url
            }]
        }
        requests.post(SLACK_POST_URL, data=json.dumps(post_json))

        
    def make2graph(self,data1,data2,label_name1,label_name2):
        fig = plt.figure(self.figure_num,figsize=(12,6))
        self.figure_num = + 1
        ax = fig.add_subplot(1,1,1)
        plt.plot(self.time_graph, data1,label=label_name1)
        plt.plot(self.time_graph, data2,label=label_name2)

        ax.xaxis.set_major_locator(self.xloc)
        ax.xaxis.set_major_formatter(self.xfmt)
        ax.set_xlim(self.today_start, self.today_end) 

        ave=np.average(data1)

        ax.set_ylim([ave*0.75,ave*1.3])
        ax.xaxis.set_minor_locator(AutoMinorLocator(2))
        plt.subplots_adjust(left=0.1, right=0.95, bottom=0.1, top=0.95)
        ax.legend()
        plt.grid()
        fig_name = self._graph_name(self.location,'Temperature')
        plt.savefig(os.path.join(self.save_dir, fig_name))
        self.push_s3_object(fig_name)
        self._put_graph_toslack(fig_name)
        plt.cla()
        plt.clf()
        plt.close()



    def makedynamicgraph(self,data,label_name,ylim=None):
        fig = plt.figure(self.figure_num,figsize=(12, 6))
        ax = fig.add_subplot(1,1,1)
        self.figure_num = + 1
        plt.plot(self.time_graph, data,label=label_name)
        xfmt = mdates.DateFormatter("%H:%M")
        xloc = mdates.HourLocator(byhour=range(0, 24, 2), tz=None)
        if ylim == None:
            ave=np.average(data)
            ax.set_ylim([ave*0.75,ave*1.3])    
        else:
            ax.set_ylim(ylim)
        
        ax.xaxis.set_major_locator(xloc)
        ax.xaxis.set_major_formatter(xfmt)
        ax.set_xlim(self.today_start, self.today_end)
        ax.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax.legend()
        plt.grid()
        fig_name = self._graph_name(self.location,label_name)
        plt.savefig(os.path.join(self.save_dir, fig_name))
        self.push_s3_object(fig_name)
        self._put_graph_toslack(fig_name)
        plt.cla()
        plt.clf()
        plt.close()


    def make_humidity_graph(self):
        self.makedynamicgraph(today_graph.humidity_graph,"Humidity",[30,120])
    def make_temp_graph(self):
        self.make2graph(today_graph.outside_graph,today_graph.inside_graph,"outside-temp","room-temp")
    def make_co2_graph(self):
        self.makedynamicgraph(today_graph.co2_graph,"CO2",[300,1500])
    def make_pressure_graph(self):
        self.makedynamicgraph(today_graph.pressure_graph,"Pressure")
    def make_human_graph(self):
        self.makedynamicgraph(raspi_1_graph.human_graph,"Human")
    

class MakeGraph1(object):
    def __init__(self, spacedata):
        self.human_graph = spacedata.human_counter
        self.counter = spacedata.counter
        self.time_graph = spacedata.time
        self.location = 'plute-room-picture'
        self.save_dir = '/tmp/'
        self.hour = [f"{num}:00" for num in range(0,24,2)]
        self.figure_num = 0
        self.today_start = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        self.today_end = self.today_start + timedelta(days=1) - timedelta(minutes=1)
        self.now = datetime.now()
        self.xfmt = mdates.DateFormatter("%H:%M")
        self.xloc = mdates.HourLocator(byhour=range(0, 24, 2), tz=None)
    def _graph_name(self,location,label_name):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(location)
        fig_name = 'figure_{0:%m%d%H%M}_{1}'.format(self.now,label_name)
        return fig_name
    def push_s3_object(self,objectname):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(self.location)
        bucket.upload_file('/tmp/{0}.png'.format(objectname), 'gragh/{0}.png'.format(objectname))
        print(objectname)

    def _put_graph_toslack(self,filename):
        url = 'https://plute-room-picture.s3-ap-northeast-1.amazonaws.com/gragh/{0}.png'.format(filename)
        print(url)
        SLACK_POST_URL = 'https://hooks.slack.com/services/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'
        _counter = self.counter
        _counter = 0 if _counter == 0 else _counter-1
        print(_counter)
        nowtime = '{0:%m月%d日%H:%M}'.format(self.time_graph[_counter])
        nowhuman = self.human_graph[_counter]
        content = f"plutoの最新の状態:\n時刻{nowtime}\n人数{nowhuman}人"

        post_json = {
            "text": content,
            "attachments": [{
            "fallback": filename,
            "text": filename,
            "color": "#36a64f", #// 'good'、'warning'、'danger' 、または 16 進数のカラーコードのいずれかになります
            "image_url": url
            }]
        }
        requests.post(SLACK_POST_URL, data=json.dumps(post_json))

    def makedynamicgraph(self,data,label_name,ylim=None):
        fig = plt.figure(self.figure_num,figsize=(12, 6))
        ax = fig.add_subplot(1,1,1)
        self.figure_num = + 1
        plt.plot(self.time_graph, data,label=label_name)
        xfmt = mdates.DateFormatter("%H:%M")
        xloc = mdates.HourLocator(byhour=range(0, 24, 2), tz=None)
        if ylim == None:
            ave=np.average(data)
            ax.set_ylim([ave*0.75,ave*1.3])    
        else:
            ax.set_ylim(ylim)
        
        ax.xaxis.set_major_locator(xloc)
        ax.xaxis.set_major_formatter(xfmt)
        ax.set_xlim(self.today_start, self.today_end)
        ax.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax.legend()
        plt.grid()
        fig_name = self._graph_name(self.location,label_name)
        plt.savefig(os.path.join(self.save_dir, fig_name))
        self.push_s3_object(fig_name)
        self._put_graph_toslack(fig_name)
        plt.cla()
        plt.clf()
        plt.close()

    def make_human_graph(self):
        self.makedynamicgraph(raspi_1_graph.human_graph,"Human",[-3,8])
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
            # keyword_data.append(round(int(self.container[i][keyword]), 1))
        return timestamp_arrays

    def _float_data_extraction(self, keyword):
        keyword_data = []
        for i in range(len(self.container)):
            #if self.container[i][""]
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
            print("success data adjust !!")
        else:
            print("failed data adjust ! --------")
        
        day_minutes = 24 * 60
        if len(raspi_1_day_data.timestamp) == day_minutes and len(raspi_2_day_data.timestamp) == day_minutes:
            pass
        else:
            raspi_1_time_adjust = self._compare_time_array(raspi_1_day_data.time)
            raspi_2_time_adjust = self._compare_time_array(raspi_2_day_data.time)
            # self.temp_max = self._data_adjust(raspi_1_day_data.temp_max, raspi_1_time_adjust)
            # self.temp_min = self._data_adjust(raspi_1_day_data.temp_min, raspi_1_time_adjust)


    # def _data_adjust(self, , time_array):
        
            
        
    def _compare_time_array(self, data_time_array):
        new_data_time_array = []
        j = 0
        for i in range(len(data_time_array)):
            if self.this_days_datetime_array[i + j] == data_time_array[i]:
                # print("{0}".format(data_time_array[i]))
                # print("{0}  {1}  True".format(self.this_days_datetime_array[i + j], data_time_array[i]))
                new_data_time_array.append(True)
            else:
                # print(" ------- error raised -------")
                for k in range(i + j, len(self.this_days_datetime_array)):
                    new_data_time_array.append(False)
                    if self.this_days_datetime_array[k] == data_time_array[i]:
                        j = k - i
                        break
                    # print("{0}  {1}  False".format(self.this_days_datetime_array[k], data_time_array[i]))
                # print(i)
        # print(len(new_data_time_array))
        # print(len(data_time_array))
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

    raspi_1_graph = MakeGraph1(today_raspi_1_data)
    raspi_1_graph.make_human_graph()
    # raspi_2_data = dynamoData('raspi_2') 
    # today_raspi_2_data = raspi_2_data.get_today_data()

    # print(today_raspi_2_data.time)
    # # print(yesterday_data.room_temperature)
    # # print(yesterday_data.counter)

    # raspi_1_data = dynamoData('raspi_1')
    # print(raspi_1_data)
    # today_raspi1_data = raspi_1_data.get_today_data()
    # print(today_raspi1_data)
    # raspi_1_graph = MakeGraph(today_raspi1_data)
    # raspi_1_graph.make_human_graph()


    # today_graph = MakeGraph(today_data)


    # today_graph.make_humidity_graph()
    # today_graph.make_temp_graph()
    # today_graph.make_co2_graph()
    # today_graph.make_pressure_graph()
    #人の人数をグラフにする。

    

    