# coding=utf8
import threading
import zmq
import sys
import datetime
import json
import os
import time
from .import sensor_list_pb2
from .import event_list_pb2
# import sensor_list_pb2
# import event_list_pb2

# 监听的ip和端口
tcp_sensor='tcp://192.168.20.213:40210'

# 传感类数据对象


class Data:
    def __init__(self, tag, data_type, quality, timestamp,
                 value_double=0.0,
                 value_int64=0,
                 value_string='',
                 value_bytes=b''):
        # 标签点名称
        self.tag = tag
        # 值
        self.value_double = value_double
        self.value_int64 = value_int64
        self.value_string = value_string
        self.value_bytes = value_bytes
        # 数据类型
        self.data_type = data_type
        # 品质
        self.quality = quality
        # 时间戳
        self.timestamp = timestamp

    def get_value(self):
        if self.data_type not in (0, 1, 2, 3):
            return None
        elif self.data_type == 0:
            return self.value_double
        elif self.data_type == 1:
            return self.value_int64
        elif self.data_type == 2:
            return self.value_string
        else:
            return self.value_bytes

# 事件类数据对象

def sdt(ts):
    da = datetime.datetime.fromtimestamp(ts)
    ymd = da.strftime("%Y-%m-%d %H:%M:%S")
    return ymd

# 传感类数据对象转字典


def sensor2dict(data):
    if data:
        value = data.get_value()
        return {'tag': data.tag,
                'value': value,
                'data_type': data.data_type,
                'quality': data.quality,
                'timestamp': sdt(data.timestamp)}
    else:
        return {}

# 事件类数据对象转字典

class SensorClient(object):

    def __init__(self,tcp_sensor=tcp_sensor):
        """Initialize Worker"""
        self.tcp_sensor = tcp_sensor
        self.sensor_list = []
        self._context = zmq.Context()
        self.sub_sensor = self._context.socket(zmq.SUB)
        self._make_thread()

    def _do_init(self):
        self.sub_sensor.connect(self.tcp_sensor)
        self.sub_sensor.setsockopt(zmq.SUBSCRIBE, b"")


    def _make_thread(self):

        self._thread = threading.Thread(target=self._run_server)
        self._thread.setDaemon(True)
        self._thread.start()

    def _run_server(self):
        print('开始初始化。。。。')
        self._do_init()
        print('初始化完成。。。')
        while True:
            self.receive_sensor_message()
            time.sleep(5)

    def un_package_sensor_data(self, msg_data):
        data_list = []
        sensors_list = sensor_list_pb2.sensor_list()
        sensors_list.ParseFromString(msg_data)
        for sensor in sensors_list.sensors:
            data = Data(sensor.tag, sensor.data_type, sensor.quality, sensor.timestamp,
                        value_double=sensor.value_double,
                        value_int64=sensor.value_int64,
                        value_string=sensor.value_string,
                        value_bytes=sensor.value_bytes)
            data_list.append(data)
        return data_list

    def receive_sensor_message(self):
        # list_sensor_temp=[]
        message = self.sub_sensor.recv()
        topic, message = message.split(b'^', 1)
        self.sensor_list= self.un_package_sensor_data(message)
        # self.sensor_list.extend(list_sensor_temp)
        # print(self.sensor_list[0].tag, self.sensor_list[0].get_value())

if __name__ == "__main__":
    z = ZClient()
    while True:
        print(len(z.sensor_list))
        for data in z.sensor_list:
            print(
                f"{sensor2dict(data)['tag']}:{sensor2dict(data)['value']}")
        time.sleep(5)
