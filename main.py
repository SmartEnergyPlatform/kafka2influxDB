# Copyright 2018 InfAI (CC SES)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

import os

from confluent_kafka import Consumer, KafkaError, TopicPartition
from influxdb import InfluxDBClient, exceptions
from objectpath import *

if os.path.isfile('./.env'):
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path)

INFLUX_HOST = os.getenv('INFLUX_HOST', "localhost")
INFLUX_PORT = os.getenv('INFLUX_PORT', 8086)
INFLUX_USER = os.getenv('INFLUX_USER', "root")
INFLUX_PW = os.getenv('INFLUX_PW', "")
INFLUX_DB = os.getenv('INFLUX_DB', "example")
KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP', "localhost:9092")
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', "topic")
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', "influx_reader")
DATA_MEASUREMENT = os.getenv('DATA_MEASUREMENT', "iot_device")
DATA_TIME_MAPPING = os.getenv('DATA_TIME_MAPPING', "time")

DATA_FILTER_TYPE = os.getenv('DATA_FILTER_TYPE', "deviceId")
DATA_FILTER_ID_MAPPING = os.getenv('DATA_FILTER_ID_MAPPING', "device_id")
DATA_FILTER_ID = os.getenv('DATA_FILTER_ID', "device_id")

DATA_FIELDS_MAPPING = os.getenv('DATA_FIELDS_MAPPING', '{"value:float": "value"}')

field_config = json.loads(DATA_FIELDS_MAPPING)


def get_field_values(field_conf, data_in):
    fields = {}
    for (key, value) in field_conf.items():
        key_conf = key.split(":")
        key = key_conf[0]
        key_type = key_conf[1]
        val = Tree(data_in).execute('$.'+value)
        if type(val) == key_type:
            fields[key] = val
        else:
            if key_type == "str":
                fields[key] = str(val)
            elif key_type == "float":
                fields[key] = float(val)
            elif key_type == "int":
                fields[key] = int(val)
    return fields


client = InfluxDBClient(INFLUX_HOST,
                        INFLUX_PORT,
                        INFLUX_USER,
                        INFLUX_PW,
                        INFLUX_DB)

client.create_database(INFLUX_DB)

c = Consumer({
    'bootstrap.servers': KAFKA_BOOTSTRAP,
    'group.id': KAFKA_GROUP_ID,
    'default.topic.config': {
        'auto.offset.reset': 'smallest'
    }})

#c.assign(TopicPartition('0', 0))

c.subscribe([KAFKA_TOPIC])
running = True
while running:
    msg = c.poll()
    if not msg.error():
        print('Received message: %s' % msg.value().decode('utf-8'))
        data_input = json.loads(msg.value().decode('utf-8'))
        if Tree(data_input).execute('$.' + DATA_FILTER_ID_MAPPING) == DATA_FILTER_ID:
            body = {
                "measurement": DATA_MEASUREMENT,
                "time": Tree(data_input).execute('$.' + DATA_TIME_MAPPING),
                "fields": get_field_values(field_config, data_input)
            }
            print(body)
            try:
                client.write_points([body])
            except exceptions.InfluxDBClientError as e:
                print(e.content)
    elif msg.error().code() != KafkaError._PARTITION_EOF:
        print(msg.error())
        running = False

c.close()

