import os

import cv2
import numpy as np
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array


class MaskDetector:
    def __init__(
            self,
            face_detection_model_dir: "os.PathLike",
            mask_detection_model: "os.PathLike",
            confidence: float = 0.5
    ):
        if not os.path.exists(face_detection_model_dir):
            raise FileNotFoundError("face detection model not found")

        prototxt_path = os.path.join(face_detection_model_dir, "deploy.prototxt")
        weights_path = os.path.join(face_detection_model_dir, "res10_300x300_ssd_iter_140000.caffemodel")
        face_detection_model_dir = cv2.dnn.readNet(prototxt_path, weights_path)
        self.face_detection_model = face_detection_model_dir

        if not os.path.exists(mask_detection_model):
            raise FileNotFoundError("mask detection model not found")
        self.mask_detection_model = load_model(mask_detection_model)

        self.confidence = confidence


    def have_mask(self, image: np.ndarray) -> bool:

        (h, w) = image.shape[:2]
        # construct a blob from the image
        blob = cv2.dnn.blobFromImage(
            image, 1.0, (300, 300),
            (104.0, 177.0, 123.0)
        )
        # pass the blob through the network and obtain the face detections
        self.face_detection_model.setInput(blob)
        detections = self.face_detection_model.forward()

        confidence = detections[0, 0, 0, 2]  # the maximum confidence

        # filter out weak detections by ensuring the confidence is
        # greater than the minimum confidence
        if confidence > self.confidence:
            # compute the (x, y)-coordinates of the bounding box for
            # the object
            box = detections[0, 0, 0, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # ensure the bounding boxes fall within the dimensions of
            # the frame
            (startX, startY) = (max(0, startX), max(0, startY))
            (endX, endY) = (min(w - 1, endX), min(h - 1, endY))

            # extract the face ROI, convert it from BGR to RGB channel
            # ordering, resize it to 224x224, and preprocess it
            face = image[startY:endY, startX:endX]
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face = cv2.resize(face, (224, 224))
            face = img_to_array(face)
            face = preprocess_input(face)
            face = np.expand_dims(face, axis=0)

            # pass the face through the model to determine if the face
            # has a mask or not
            (mask, withoutMask) = self.mask_detection_model.predict(face)[0]
            return mask > withoutMask


mask_detector = MaskDetector("face_detection_model", "mask_detector.model")