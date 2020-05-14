import os
import time
import json
import signal
import logging
import json
import random
import paho.mqtt.client as mqtt
import threading
import concurrent.futures
import base64
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2

# Global vars
config = None
secret = None
executor = None
remotes = {}
sensor_keys = {}

# configure logger output format
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',datefmt='%m-%d %H:%M:%S')
# get a logger to write
logger = logging.getLogger('gateway')

def _get_sensor_key(uuid):
    global sensor_keys
    if uuid not in sensor_keys:
        sensor_keys[uuid] = base64.b64encode(PBKDF2(secret['secret_key'] + uuid, secret['secret_salt'], 16, config['security']['kdf_iterations'], None)).decode('utf-8')
    return sensor_keys[uuid]

def _decrypt(uuid, message):
    cipher = AES.new(_get_sensor_key(uuid), AES.MODE_CFB, message[:16])
    return cipher.decrypt(message[16:])

def on_local_message(client, userdata, message):
    if config['local']['telemetry_topic'] in message.topic:
        dev_id = message.topic[len(config['local']['telemetry_topic']) + 1:]

        try:
            msg = _decrypt(dev_id, base64.b64decode(message.payload))
            value = json.loads(msg)[config['local']['value_description']]
        except:
            logger.info('[local] Received malformed message on topic %s', msg, message.topic)

        logger.info('[local] Received message %s on topic %s', msg, message.topic)
        executor.submit(remote_publish, dev_id, value)

def remote_publish(dev_id, value):
    global remotes
    remote = None

    # MQTT client - remote
    if (dev_id not in remotes) or (not remotes[dev_id].is_connected()):
        remote = mqtt.Client(dev_id + '_' + str(random.randint(0, 5000)), protocol=mqtt.MQTTv311)
        remote.username_pw_set(config['remote']['device_prefix']+dev_id+'@'+config['remote']['tenant_id'], password=secret['hono_sensors_pw'])
        remote.enable_logger()
        remote.connect(config['remote']['host'], port=config['remote']['port'])
        remotes[dev_id] = remote
    else:
        remote = remotes[dev_id]

    msg = json.dumps({config['remote']['value_description']: value})
    logger.info("Publishing: " + msg)
    remote.publish(config['remote']['telemetry_topic'], msg, qos=0)


def remotes_loop():
    while True:
        r = remotes.copy()
        for remote in r:
            r[remote].loop()
        time.sleep(1)


def main():
    global config, secret, executor

    try:
        with open('gateway_config.json') as json_file:
            config = json.load(json_file)
        with open('.secret_config.json') as json_file:
            secret = json.load(json_file)
            secret['secret_salt'] = secret['secret_salt'].encode('utf-8')
    except:
        logger.error("Config files could not be read")
        return

    logger.info("Config files successfully read")

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=config['local']['max_workers'])

    # MQTT client - local
    local = mqtt.Client('', protocol=mqtt.MQTTv311)
    local.on_message = lambda cl,ud,ms: executor.submit(on_local_message, cl, ud, ms)
    local.username_pw_set(config['local']['uname'], password=secret['local_broker_pw'])
    local.enable_logger()
    logger.info('[local] Connect to %s, %d', config['local']['host'], config['local']['port'])
    local.connect(config['local']['host'], port=config['local']['port'])
    local.subscribe(config['local']['telemetry_topic'] + '/#', qos=0)

    remotes_th = threading.Thread(target=remotes_loop)
    remotes_th.start()
    local.loop_forever()

    local.unsubscribe(config['local']['telemetry_topic'] + '/#')
    local.loop_stop()
    local.disconnect()

    for dev_id in remotes:
        remotes[dev_id].disconnect()

    return 0


if __name__ == '__main__':
    main()
