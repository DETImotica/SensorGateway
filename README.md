# Sensor_Gateway
Code and Config files for a Raspberry Pi MQTT bridge

## Installation

1. Install docker
```
sudo apt install docker
```

2. Pull the eclipse-mosquitto image
```
docker pull eclipse-mosquitto
```

3. Create the necessary directories
```
mkdir -p /var/mosquitto/logs
mkdir -p /var/mosquitto/data
chmod ugw+w /var/mosquitto
```

4. Create the configuration and passwd files

5. Start a docker container in daemon mode
```
docker run -d -it -p 1883:1883 -p 9001:9001 -v /root/mosquitto.conf:/mosquitto/config/mosquitto.conf -v /var/mosquitto/data:/mosquitto/data -v /var/mosquitto/log:/mosquitto/log eclipse-mosquitto
```

6. (Optional) Install mosquitto-clients package to be able to subscribe and publish to topics via the CLI
```
sudo apt install mosquitto-clients
```

## Usage

#### Credentials (temporary)
Username: **detimotic**

Password: **testpw**  

#### Subscribing to topics
Using *mosquitto-clients*:
```
mosquitto_sub -h <address> -v -t "<topic>" -u detimotic -P testpw
```
Replace *\<topic\>* for the desired topic
 
Replace *\<address\>* for the IP address of the gateway or *localhost* if done on the gateway itself  


#### Publishing to topics
Using *mosquitto-clients*:
```
mosquitto_pub -h <address> -t "<topic>" -u detimotic -P testpw -m "<message>"
```
Replace *\<topic\>* for the desired topic
 
Replace *\<address\>* for the IP address of the gateway or *localhost* if done on the gateway itself   


## References
- https://selfhostedhome.com/using-two-mqtt-brokers-with-mqtt-broker-bridging/
