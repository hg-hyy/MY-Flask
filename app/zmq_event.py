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

tcp_event='tcp://192.168.20.213:40220'


# 事件类数据对象
class Event:
    def __init__(self, source, event_type, level, keyword, content, timestamp):
        # 事件源
        self.source = source
        # 事件类型
        self.event_type = event_type
        # 等级
        self.level = level
        # 摘要
        self.keyword = keyword
        # 内容
        self.content = content
        # 时间戳
        self.timestamp = timestamp


def sdt(ts):
    da = datetime.datetime.fromtimestamp(ts)
    ymd = da.strftime("%Y-%m-%d %H:%M:%S")
    return ymd

# 事件类数据对象转字典
def event2dict(event):
    if event:
        return {'source': event.source,
                'event_type': event.event_type,
                'level': event.level,
                'keyword': event.keyword,
                'content': event.content,
                'timestamp': sdt(event.timestamp)}
    else:
        return {}

class EventClient(object):

    def __init__(self,tcp_event=tcp_event):
        """Initialize Worker"""
        self.tcp_event = tcp_event
        self.event_list = []
        self._context = zmq.Context()
        self.sub_event = self._context.socket(zmq.SUB)
        self._make_thread()

    def _do_init(self):
        self.sub_event.connect(self.tcp_event)
        self.sub_event.setsockopt(zmq.SUBSCRIBE, b"")

    def _make_thread(self):

        self._thread = threading.Thread(target=self._run_server)
        self._thread.setDaemon(True)
        self._thread.start()

    def _run_server(self):
        self._do_init()
        while True:
            self.receive_event_message()
            time.sleep(5)

    def un_package_event_data(self, msg_data):
        data_list = []
        event_list = event_list_pb2.event_list()
        event_list.ParseFromString(msg_data)
        for event in event_list.events:
            data = Event(event.source, event.event_type, event.level,
                         event.keyword, event.content, event.timestamp)
            data_list.append(data)
        return data_list

    def receive_event_message(self):
        list_event_temp = []
        message = self.sub_event.recv()
        topic, message = message.split(b'^', 1)
        list_event_temp = self.un_package_event_data(message)
        self.event_list.extend(list_event_temp)


if __name__ == "__main__":
    z = ZClient()
    while True:
        print(len(z.event_list))
        for data in z.event_list:
            print(
                f"{event2dict(data)['timestamp']}:{event2dict(data)['content']}")
        time.sleep(5)
