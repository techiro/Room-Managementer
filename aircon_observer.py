import weather_receive as weather
import random

def air_con_cheacker(first_temp, end_temp, out_temp):
    delta_room_temp_threshold = 1
    delta_temp_threshold = 3
    if abs(first_temp - end_temp) < delta_temp_threshold and abs(end_temp - out_temp) > delta_temp_threshold:
        print("air_con on !!")
    else:
        print("air_con off ")


    print(on_temp_num)
    print(off_temp_num)

if __name__ == "__main__":
    weather_data = weather.Weather_api_data()
    weather_data.get_weather_data()
    temp = weather_data.read_temperature()
    print(temp)
    # テストデータ用意
    on_temp_num = []
    off_temp_num = []
    for i in range(1, 31):
        on_temp_num.append(random.uniform(25.5, 26.5))
        off_temp_num.append(abs(temp - 26)/30 * i + 25.5)

    # エアコンの消し忘れ検知
    # 外気温との差が縮まらない
    print("if airconditioner on's  test")
    air_con_cheacker(on_temp_num[0], on_temp_num[29], temp)

    print("if airconditioner off's  test")
    air_con_cheacker(off_temp_num[0], off_temp_num[29], temp)

