import imp
import os
from datetime import datetime
from pathlib import Path

import cv2
import paho.mqtt.client as mqtt

from mask_detector import MaskDetector
from secrets import MQTT_USER, MQTT_PASSWORD

MQTT_SERVER = "mosquitto.itsloop.dev"
MQTT_TOPIC_IMAGE = "esp32/iust_image"
MQTT_TOPIC_RESULT = "esp32/iust_out"

IMAGE_TMP_DIR = Path("./img_tmp")


def on_connect(client, userdata, flags, rc):
    print(f"[INFO] {datetime.now().time()} - Connectd to server")
    client.subscribe(MQTT_TOPIC_IMAGE)


def on_message(client, userdata, msg):
    now = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    name = IMAGE_TMP_DIR / f"image_{now}.jpg"

    with open(name, "wb") as fd:
        fd.write(msg.payload)

    image = cv2.imread(name, -1)
    if image is None:
        return

    res = mask_det.have_mask(image)
    if res is not None:
        client.publish(MQTT_TOPIC_RESULT, "1" if res else "0")
        print(f"[INFO] {datetime.now().time()} - Mask detection result: {res}")


if __name__ == "__main__":

    if not os.path.exists(IMAGE_TMP_DIR):
        IMAGE_TMP_DIR.mkdir(parents=True)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.connect(MQTT_SERVER, 1883, 65535)
    client._sock.setblocking(1)
    mask_det = MaskDetector(
        "./face_detection_model", "./mask_detection_model/mask_detector.model"
    )
    print(f"[INFO] {datetime.now().time()} - Loading models...")
    client.loop_forever()
