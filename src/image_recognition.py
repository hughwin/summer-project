import io
import os

from google.cloud import vision
from google.oauth2 import service_account

import settings

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(settings.BASE_DIRECTORY / "gcp_cred.json")
credentials = service_account.Credentials.from_service_account_file(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))


def localize_objects(input_image):
    """Detects objects in the image"""
    vision_client = vision.ImageAnnotatorClient()

    with open(input_image, 'rb') as image_file:
        content = image_file.read()
    image = vision.types.Image(content=content)

    objects = vision_client.object_localization(
        image=image).localized_object_annotations

    return_string = ""
    for object_ in objects:
        return_string += "\n{} (confidence: {})".format(object_.name, object_.score)
    return return_string


def detect_landmarks(input_image):
    """Detects landmarks in the file."""
    vision_client = vision.ImageAnnotatorClient()

    with io.open(input_image, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = vision_client.landmark_detection(image=image)
    landmarks = response.landmark_annotations

    return_string = ""

    for landmark in landmarks:
        return "Looks like the" + landmark.description + "\n\n"
    return return_string


def detect_labels(input_image):
    """Detects labels in the file."""
    vision_client = vision.ImageAnnotatorClient()

    with io.open(input_image, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = vision_client.label_detection(image=image)
    labels = response.label_annotations
    return_string = ""

    for label in labels:
        return_string += label.description
    return return_string + "\n\n"
