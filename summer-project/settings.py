import os
from pathlib import Path


ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
CLIENT_KEY = os.environ["CLIENT_KEY"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
NASA = os.environ["NASA"]
BASE_ADDRESS = "https://hostux.social/"
NASA_ADDRESS_IMAGES = "https://api.nasa.gov/planetary/apod?api_key=%s"
TOO_MANY_REQUESTS_MESSAGE = "You're making too many requests!"
JSON_ERROR_MESSAGE = "Decoding JSON has failed"
INVALID_COMMAND = "Command not recognised. Type \"@botbot help\" for a list of commands"
MAX_MESSAGE_LENGTH = 500
ROTATE_COMMAND = "rotate"
ROTATE_SIMPLE = "simple"
DIRECTORY = Path.cwd()
INPUT_FOLDER = DIRECTORY / "input"
OUTPUT_FOLDER = DIRECTORY / "output"
JPEG_INPUT = str(INPUT_FOLDER / "{}.jpeg")
JPEG_OUTPUT = str(OUTPUT_FOLDER / "{}.jpeg")
PNG_OUTPUT = str(OUTPUT_FOLDER / "{}.png")
BMP_OUTPUT = str(OUTPUT_FOLDER / "{}.bmp")
TESSERACT_PATH = r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract"
HELP_MESSAGE = "Welcome to my image processing bot!" \
    "\nThe bot can perform simple (and not so simple) image transformations." \
    "\nCommands:" \
    "\nHelp - get help" \
    "\nAbout - get information about your image" \
    "\nDecolourise - returns a decolourised version of your image" \
    "\nText - get the text from your image" \
    "\nPreserve <colour> - preserve a colour channel" \
    "\nHistogram - generate a histogram of your image" \
    "\nRotate <degrees> <simple> - rotates an image by the specified number of degrees. The optional parameter " \
               "\"simple\" will cause the rotation to crop parts of the image."

