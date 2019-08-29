import smbus

def measure_lux():
    bus = smbus.SMBus(1)
    address = 0x23
    lux = bus.read_i2c_block_data(address, 0x10)
    return (lux[0]*256+lux[1])/1.2
