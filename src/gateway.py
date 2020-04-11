import os
import time
import json
import signal
import logging
import argparse
import json
import random
import paho.mqtt.client as mqtt

# Global vars
config = None
remotes = {}

# configure logger output format
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',datefmt='%m-%d %H:%M:%S')
# get a logger to write
logger = logging.getLogger('gateway')

def on_local_message(client, userdata, message):
    msg = message.payload.decode("utf-8")
    logger.info('[local] Received message %s on topic %s', msg, message.topic)
    value = json.loads(msg)[config['local']['value_description']]
    if config['local']['telemetry_topic'] in message.topic:
        dev_id = message.topic[len(config['local']['telemetry_topic']) + 1:]
        remote_publish(dev_id, value)
    elif config['local']['events_topic'] in message.topic:
        dev_id = message.topic[len(config['local']['events_topic']) + 1:]
        remote_publish(dev_id, value, True)


def remote_publish(dev_id, value, event=False):
    global remotes
    remote = None

    # MQTT client - remote
    if (dev_id not in remotes) or (not remotes[dev_id].is_connected()):
        if dev_id in remotes:
            remotes[dev_id].loop_stop()
        remote = mqtt.Client(dev_id + '_' + str(random.randint(0, 5000)), protocol=mqtt.MQTTv311)
        remote.username_pw_set(config['remote']['device_prefix']+dev_id+'@'+config['remote']['tenant_id'], password=args.p)
        remote.enable_logger()
        remote.connect(config['remote']['host'], port=config['remote']['port'])
        remotes[dev_id] = remote
        remote.loop_start()
    else:
        remote = remotes[dev_id]

    msg = json.dumps({config['remote']['value_description']: value})
    logger.info("Publishing: " + msg)
    remote.publish(config['remote']['events_topic' if event else 'telemetry_topic'], msg, qos=0)


def main(args):
    global config

    with open('gateway_config.json') as json_file:
        config = json.load(json_file)

    logger.info("Config file successfully read")

    # MQTT client - local
    local = mqtt.Client('', protocol=mqtt.MQTTv311)
    local.on_message = on_local_message
    local.username_pw_set(config['local']['uname'], password="testpw")    # Temporary
    local.enable_logger()
    logger.info('[local] Connect to %s, %d', config['local']['host'], config['local']['port'])
    local.connect(config['local']['host'], port=config['local']['port'])
    local.subscribe(config['local']['telemetry_topic'] + '/#', qos=0)
    local.subscribe(config['local']['events_topic'] + '/#', qos=0)
    local.loop_forever()

    local.unsubscribe(config['local']['telemetry_topic'] + '/#')
    local.unsubscribe(config['local']['events_topic'] + '/#')
    local.loop_stop()
    local.disconnect()

    for dev_id in remotes:
        remotes[dev_id].disconnect()

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DETImotic Gateway')
    parser.add_argument('-p', type=str, help='password', default='<DEVICE_PASSWORD>')
    args = parser.parse_args()
    main(args)
