import smbus

def measure_lux():
    try:
        bus = smbus.SMBus(1)
        address = 0x23
        lux = bus.read_i2c_block_data(address, 0x10)
    except:
        print("illuminance.py measure_lux() raised error !!")
        print("照度センサーの接続を確認してください。")
    return (lux[0]*256+lux[1])/1.2
