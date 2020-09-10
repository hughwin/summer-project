import io
import os

from google.cloud import vision
from google.oauth2 import service_account

import settings

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(settings.BASE_DIRECTORY / "gcp_cred.json")
credentials = service_account.Credentials.from_service_account_file()


def detect_faces(image):
    print("faces called")
    vision_client = vision.ImageAnnotatorClient()

    with io.open(image, 'rb') as image_file:
        content = image_file.read()

    image = vision_client.image(content=content)

    faces = image.detect_faces()

    return_string = "Faces: "
    for face in faces:
        return_string += "anger: {}".format(face.emotions.anger) + "\n" + \
                         "joy: {}".format(face.emotions.joy) + "\n" + \
                         "surprise: {}".format(face.emotions.surprise) + "\n"
        print(return_string)
    return return_string

#
# def detect_faces_cloud_storage(uri):
#     """Detects faces in the file located in Google Cloud Storage."""
#     vision_client = vision.Client()
#     image = vision_client.image(source_uri=uri)
#
#     faces = image.detect_faces()
#
#     print('Faces:')
#     for face in faces:
#         print('anger: {}'.format(face.emotions.anger))
#         print('joy: {}'.format(face.emotions.joy))
#         print('surprise: {}'.format(face.emotions.surprise))
#
#
# def detect_labels(path):
#     """Detects labels in the file."""
#     vision_client = vision.Client()
#
#     with io.open(path, 'rb') as image_file:
#         content = image_file.read()
#
#     image = vision_client.image(content=content)
#
#     labels = image.detect_labels()
#
#     print('Labels:')
#     for label in labels:
#         print(label.description)
#         print vars(label)
#
#
# def detect_labels_cloud_storage(uri):
#     """Detects labels in the file located in Google Cloud Storage."""
#     vision_client = vision.Client()
#     image = vision_client.image(source_uri=uri)
#
#     labels = image.detect_labels()
#
#     print('Labels:')
#     for label in labels:
#         print(label.description)
#
#
# def detect_landmarks(path):
#     """Detects landmarks in the file."""
#     vision_client = vision.Client()
#
#     with io.open(path, 'rb') as image_file:
#         content = image_file.read()
#
#     image = vision_client.image(content=content)
#
#     landmarks = image.detect_landmarks()
#
#     print('Landmarks:')
#     for landmark in landmarks:
#         print(landmark.description)
#         print vars(landmark)
#
#
# def detect_landmarks_cloud_storage(uri):
#     """Detects landmarks in the file located in Google Cloud Storage."""
#     vision_client = vision.Client()
#     image = vision_client.image(source_uri=uri)
#
#     landmarks = image.detect_landmarks()
#
#     print('Landmarks:')
#     for landmark in landmarks:
#         print(landmark.description)
#
#
# def detect_logos(path):
#     """Detects logos in the file."""
#     vision_client = vision.Client()
#
#     with io.open(path, 'rb') as image_file:
#         content = image_file.read()
#
#     image = vision_client.image(content=content)
#
#     logos = image.detect_logos()
#
#     print('Logos:')
#     for logo in logos:
#         print(logo.description)
#         print vars(logo)
#
#
# def detect_logos_cloud_storage(uri):
#     """Detects logos in the file located in Google Cloud Storage."""
#     vision_client = vision.Client()
#     image = vision_client.image(source_uri=uri)
#
#     logos = image.detect_logos()
#
#     print('Logos:')
#     for logo in logos:
#         print(logo.description)
#
#
# def detect_safe_search(path):
#     """Detects unsafe features in the file."""
#     vision_client = vision.Client()
#
#     with io.open(path, 'rb') as image_file:
#         content = image_file.read()
#
#     image = vision_client.image(content=content)
#
#     safe_searches = image.detect_safe_search()
#     print('Safe search:')
#     for safe in safe_searches:
#         print('adult: {}'.format(safe.adult))
#         print('medical: {}'.format(safe.medical))
#         print('spoofed: {}'.format(safe.spoof))
#         print('violence: {}'.format(safe.violence))
#         print vars(safe)
#
#
# def detect_safe_search_cloud_storage(uri):
#     """Detects unsafe features in the file located in Google Cloud Storage."""
#     vision_client = vision.Client()
#     image = vision_client.image(source_uri=uri)
#
#     safe_searches = image.detect_safe_search()
#     print('Safe search:')
#     for safe in safe_searches:
#         print('adult: {}'.format(safe.adult))
#         print('medical: {}'.format(safe.medical))
#         print('spoofed: {}'.format(safe.spoof))
#         print('violence: {}'.format(safe.violence))
#
#
# def detect_text(path):
#     """Detects text in the file."""
#     vision_client = vision.Client()
#
#     with io.open(path, 'rb') as image_file:
#         content = image_file.read()
#
#     image = vision_client.image(content=content)
#
#     texts = image.detect_text()
#     print('Texts:')
#     for text in texts:
#         print(text.description)
#         print vars(text)
#
#
# def detect_text_cloud_storage(uri):
#     """Detects text in the file located in Google Cloud Storage."""
#     vision_client = vision.Client()
#     image = vision_client.image(source_uri=uri)
#
#     texts = image.detect_text()
#     print('Texts:')
#     for text in texts:
#         print(text.description)
#
#
# def detect_properties(path):
#     """Detects image properties in the file."""
#     vision_client = vision.Client()
#
#     with io.open(path, 'rb') as image_file:
#         content = image_file.read()
#
#     image = vision_client.image(content=content)
#
#     properties = image.detect_properties()
#     print('Properties:')
#     for prop in properties:
#         color = prop.colors[0]
#         print('fraction: {}'.format(color.pixel_fraction))
#         print('r: {}'.format(color.color.red))
#         print('g: {}'.format(color.color.green))
#         print('b: {}'.format(color.color.blue))
#         print vars(properties)
#
#
# def detect_properties_cloud_storage(uri):
#     """Detects image properties in the file located in Google Cloud Storage."""
#     vision_client = vision.Client()
#     image = vision_client.image(source_uri=uri)
#
#     properties = image.detect_properties()
#     for prop in properties:
#         color = prop.colors[0]
#         print('fraction: {}'.format(color.pixel_fraction))
#         print('r: {}'.format(color.color.red))
#         print('g: {}'.format(color.color.green))
#         print('g: {}'.format(color.color.blue))
#
#
# def run_all_local():
#     """Runs all available detection operations on the local resources."""
#     file_name = os.path.join(
#         os.path.dirname(__file__),
#         'resources/wakeupcat.jpg')
#     detect_labels(file_name)
#
#     file_name = os.path.join(
#         os.path.dirname(__file__),
#         'resources/landmark.jpg')
#     detect_landmarks(file_name)
#
#     file_name = os.path.join(
#         os.path.dirname(__file__),
#         'resources/face_no_surprise.jpg')
#     detect_faces(file_name)
#
#     file_name = os.path.join(
#         os.path.dirname(__file__),
#         'resources/logos.png')
#     detect_logos(file_name)
#
#     file_name = os.path.join(
#         os.path.dirname(__file__),
#         'resources/wakeupcat.jpg')
#     detect_safe_search(file_name)
#
#     ''' TODO: Uncomment when https://goo.gl/c47YwV is fixed
#     file_name = os.path.join(
#         os.path.dirname(__file__),
#         'resources/text.jpg')
#     detect_text(file_name)
#     '''
#
#     file_name = os.path.join(
#         os.path.dirname(__file__),
#         'resources/landmark.jpg')
#     detect_properties(file_name)
