import io
import json
import os

from google.cloud import vision
from google.oauth2 import service_account

import settings


class ImageRecognition:

    def __init__(self):
        self.credentials = None
        self.vision_client = None

    def start(self):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json.load(str(settings.BASE_DIRECTORY / "gcp_cred.json"))
        self.credentials = service_account.Credentials.from_service_account_file \
            (os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
        self.vision_client = vision.ImageAnnotatorClient()

    def localize_objects(self, input_image):
        """Detects objects in the image"""

        with open(input_image, 'rb') as image_file:
            content = image_file.read()
        image = vision.types.Image(content=content)

        objects = self.vision_client.object_localization(
            image=image).localized_object_annotations

        return_string = ""
        for object_ in objects:
            return_string += "\n{} (confidence: {})".format(object_.name, object_.score)
        return return_string

    def detect_landmarks(self, input_image):
        """Detects landmarks in the file."""

        with io.open(input_image, 'rb') as image_file:
            content = image_file.read()

        image = vision.types.Image(content=content)

        response = self.vision_client.landmark_detection(image=image)
        landmarks = response.landmark_annotations

        return_string = ""

        for landmark in landmarks:
            return "Looks like the " + landmark.description + "\n\n"
        return return_string

    def detect_labels(self, input_image):
        """Detects labels in the file."""

        with io.open(input_image, 'rb') as image_file:
            content = image_file.read()

        image = vision.types.Image(content=content)

        response = self.vision_client.label_detection(image=image)
        labels = response.label_annotations
        return_string = ""

        for label in labels:
            return_string += label.description + "\n"
        return return_string + "\n\n"
