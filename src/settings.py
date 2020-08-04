import os
from pathlib import Path

# ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
# CLIENT_KEY = os.environ["CLIENT_KEY"]
# CLIENT_SECRET = os.environ["CLIENT_SECRET"]
# NASA = os.environ["NASA"]
BASE_ADDRESS = "https://hostux.social/"
NASA_ADDRESS_IMAGES = "https://api.nasa.gov/planetary/apod?api_key=%s"
TOO_MANY_REQUESTS_MESSAGE = "You're making too many requests!"
JSON_ERROR_MESSAGE = "Decoding JSON has failed"
INVALID_COMMAND = "Command not recognised. Type \"@botbot help\" for a list of commands"
MAX_MESSAGE_LENGTH = 500
ROTATE_COMMAND = "rotate"
ROTATE_SIMPLE = "simple"
BASE_DIRECTORY = Path.cwd() / "src"
INPUT_FOLDER = BASE_DIRECTORY / "input"
RESOURCES_FOLDER = BASE_DIRECTORY / "resources"
DAILY_IMAGE = str(BASE_DIRECTORY / "output" / "image.jpeg")
HISTOGRAM_JPEG = (str(INPUT_FOLDER / "histogram-{}.jpeg"))
JPEG_INPUT = str(INPUT_FOLDER / "{}.jpeg")
PNG_OUTPUT = str(INPUT_FOLDER / "{}.png")
BMP_OUTPUT = str(INPUT_FOLDER / "{}.bmp")
TESSERACT_PATH = r"./.apt/usr/share/tesseract-ocr/4.00/tessdata"
HELP_MESSAGE = "Welcome to my image processing bot!" \
               "\nThe bot can perform simple (and not so simple) image transformations." \
               "\nCommands:" \
               "\nHelp - get help" \
               "\nAbout - get information about your image(s)" \
               "\nDecolourise - returns a decolourised version of your image(s)" \
               "\nPreserve <colour> - preserve a colour channel" \
               "\nHistogram - generate a histogram of your image(s)" \
               "\nRotate <degrees> <simple> - rotates an image by the specified number of degrees. The optional " \
               "parameter " \
               "\"simple\" will cause the rotation to crop parts of the image." \
               "\nEnhance - sharpen the image" \
               "\nBorder - will add a border to your image(s)" \
               "\nCrop - will crop your image(s)" \
               "\nBrightness <value> - adjust the brightness of your image(s). If no" \
               "value is supplied, the default value (1.5) will be used." \
               "\nContrast <value> - adjust the contrast of your image(s). If no " \
               "value is supplied, the default value (1.5) will be used." \
               "\nColour <value> - adjust the colour of your image(s). If no " \
               "value is supplied, the default value (1.5) will be used." \
               "\nMirror - create a mirrored version of your images(s)" \
               "\nFlip - create a flipped version of your image(s)" \
               "\nTransparent - create a transparent version of your image(s). Will return a .png image" \
               "\nNegative - create a negative of your image(s)" \
               "\nSepia - create a sepia version of your image(s)" \
               "\nBlur - create a blurred version of your image(s)" \
               "\nBlurred - blur the borders of your image(s)" \
               "\nBorder - add a border to your image" \
               "\nPNG - convert your image(s) to PNG format" \
               "\nBMP - convert your images to BMP format"

