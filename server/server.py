import os
from datetime import datetime
from pathlib import Path
from secrets import MQTT_PASSWORD, MQTT_USER

import cv2
import paho.mqtt.client as mqtt

from mask_detector import MaskDetector
from db import DB

MQTT_SERVER = "mosquitto.itsloop.dev"
MQTT_TOPIC_IMAGE = "esp32/iust_image"
MQTT_TOPIC_RESULT = "esp32/iust_out"

IMAGE_TMP_DIR = Path("./img_tmp")

image_log = {'recieved': False, 'result': None, "file_name": None}


def on_connect(client, userdata, flags, rc):
    print(f"[INFO] {datetime.now().time()} - Connectd to server")
    client.subscribe(MQTT_TOPIC_IMAGE)


def on_message(client, userdata, msg):
    global image_log

    if len(msg.payload) <= 32:
        temperature = int(msg.payload)

        if not image_log['recieved']:
            return

        print(temperature)

        if image_log["result"] is None:  # no face detected
                client.publish(MQTT_TOPIC_RESULT, "-1")
        elif image_log["result"] and temperature < 37:  # mask detected and temperature is below 37
                client.publish(MQTT_TOPIC_RESULT, "1")
        else:  # mask not detected or temperature is above 37
                client.publish(MQTT_TOPIC_RESULT, "0")

        current_time = datetime.now()
        print(f"[INFO] {current_time.time()} - Mask: {image_log['result']} | Temp: {temperature}")
        
        DB.add_new_record(current_time.timestamp(), image_log["file_name"], image_log["result"], temperature)

        image_log = {'recieved': False, 'result': None, "file_name": None}

    else:
        now = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        name = str(IMAGE_TMP_DIR / f"image_{now}.jpg")

        with open(name, "wb") as fd:
            fd.write(msg.payload)

        image = cv2.imread(name, -1)

        if image is None:
            res = None
        else:
            res = mask_det.have_mask(image)

        image_log['recieved'] = True
        image_log['result'] = res
        image_log["file_name"] = name


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
