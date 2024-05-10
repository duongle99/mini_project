import serial.tools.list_ports
import random
import time
import sys
from string import Template
from Adafruit_IO import MQTTClient


AIO_FEED_IDS = ["bbc-led", "bbc-humi", "bbc-hir"]
AIO_USERNAME = "dlhcmut"
AIO_KEY = ""

def connected(client):
    print("Kết nối thành công...")
    for feed in AIO_FEED_IDS:
        client.subscribe(feed)

def subscribe(client, userdata, mid, granted_qos):
    print("Subcribe thành công...")

def disconnected(client):
    print("Ngắt kết nối...")
    sys.exit(1)

def message(client, feed_id, payload):
    if feed_id == "bbc-led":
        if payload == "0":
            uart_write("1")
        else:
            uart_write("2")
    elif feed_id == "bbc-fan":
        if payload == "2":
            uart_write("3")
        else:
            uart_write("4")
    elif feed_id == "fire-alarm":
        uart_write(payload)
    if isMicrobitConnected:
        ser.write((str(payload) + "#").encode())

def uart_write(data):
    ser.write(str(data).encode())

client = MQTTClient(AIO_USERNAME, AIO_KEY)
client.on_connect = connected
client.on_disconnect = disconnected
client.on_message = message
client.on_subscribe = subscribe
client.connect()
client.loop_background()

def getPort():
    ports = serial.tools.list_ports.comports()
    N = len(ports)
    commPort = "None"
    for i in range(0, N):
        port = ports[i]
        strPort = str(port)
        if "USB-SERIAL" in strPort:
            splitPort = strPort.split(" ")
            commPort = (splitPort[0])
    print(commPort)
    return "COM5"

isMicrobitConnected = False
if getPort() != "None":
    ser = serial.Serial(port=getPort(), baudrate=115200)
    isMicrobitConnected = True

def processData(data):
    data = data.replace("!", "")
    data = data.replace("#", "")
    print(data)
    splitData = data.split(":")
    try:
        if splitData[0] == "HIR":
            client.publish("bbc-hir", splitData[1])
        if splitData[2] == "TEMP":
            client.publish("bbc-temp", splitData[3])
        if splitData[4] == "HUMI":
            client.publish("bbc-humi", splitData[5])
            x = Template('{"temp": $temp, "humidity": $humidity}')
            st = x.substitute(temp=splitData[3], humidity=splitData[5])
            client.publish("value", st)
    except:
        pass

def generateRandomData():
    random_temp = round(random.uniform(20.0, 30.0), 2)
    random_humi = round(random.uniform(40.0, 60.0), 2)
    return f"HIR:RandomData:TEMP:{random_temp}:HUMI:{random_humi}"

def readSerial():
    bytesToRead = ser.inWaiting()
    if bytesToRead > 0:
        global mess
        mess = mess + ser.read(bytesToRead).decode("UTF-8")
        while "#" in mess and "!" in mess:
            start = mess.find("!")
            end = mess.find("#")
            processData(mess[start:end + 1])
            if end == len(mess):
                mess = ""
            else:
                mess = mess[end + 1:]

def processDataRandomly():
    random_data = generateRandomData()
    processData(random_data)

mess = ""
while True:
    if isMicrobitConnected:
        readSerial()
    processDataRandomly()
    time.sleep(10)
