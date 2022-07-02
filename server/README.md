# Server

## The `on_connect` MQTT API
This function is the callback for when the client receives acknoledgement from the server. Here it logs the connection establishment and the client subscribes on the `MQTT_TOPIC_IMAGE` topic.

## The `on_message` MQTT API
This function is the callback function for when the client receives a publish message from the server.

### Here we have two types of messages.
Both types are sent as `byte` arrays using the `MQTT` protocol.
The type of the message is checked and handled by the size of the message received from the server.

- Image
- Tempratrue


If the received message is of type image, it is written to a file with the name of `image_<current_datetime>`. The image is validated using the python `opencv` module and the `imread` fucntion. If the file is an image then it goes through the deep learning model to detect if a face has been recognized, and whether or not a mask is on that face. If so the response to the server will be accordingly.
The temperature is saved in a varaible. The response depends on the extracted information from the image. If there is no face in the image, regardless of the temperature, the result `-1` is published with the `MQTT_TOPIC_RESULT`, If there is a mask and the temperature is lower than 37, the result is `1`, otherwise the result is set to `0`.
Then the image, the temperature and the result is recorded to a `SQLite` database instance.
