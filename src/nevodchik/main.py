import os

mqtt_host = os.environ.get("MQTT_HOST")
mqtt_port = os.environ.get("MQTT_PORT")
mqtt_user = os.environ.get("MQTT_USER")
mqtt_pass = os.environ.get("MQTT_PASS")


def run():
    print("Fisherman is catching fish...")
    print("Host={}:{}, User={}:{}".format(mqtt_host, mqtt_port, mqtt_user, mqtt_pass))
    pass