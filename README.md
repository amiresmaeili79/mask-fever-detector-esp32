# Mask And Fever Detector ESP32 - CAM

Embedded Systems project for Spring 2022.  
This project is deployed on **esp32-cam** and a desktop pc.

## Architecture
This project consists of two main sections.   
1. Client: ESP32-CAM
2. Server: A Desktop PC

In every iteration client takes a photo and sends it to the server via **MQTT** protocol. Server retreives the image and gives it to the trained model and finds out if the image has **a face with mask or not**.
Server code resides in ```server``` directory with all its dependencies, and the rest of directories are for client.

## Deployment
In order to deploy the project do as following.
### Server
```sh
cd server
python3 -m venv [venv_name] # create a new venv [optional]
pip install -r requirements.txt # install requirements
```
Now create a file named ```secrets.py``` in ```server``` directory. Place following code in it.
```
MQTT_USER = "[user]"
MQTT_PASSWORD = "[pass]"
```
This section can be skipped if you are using a free MQTT server (change the **broker** in ```server.py```).
Now you can run server.
```sh
python3 server.py
```

### Client
Create a file ```include/secrets.h``` and put this code in it.
```c++
const char *MQTT_USER = "";
const char *MQTT_PASS = "";
const char *CLIENT_ID = "";
```
Now put ESP32-CAM in the **write mode** and build and upload the code.
Now disable write mode and run the code.