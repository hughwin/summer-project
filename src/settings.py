from pathlib import Path

# ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
# CLIENT_KEY = os.environ["CLIENT_KEY"]
# CLIENT_SECRET = os.environ["CLIENT_SECRET"]
# NASA = os.environ["NASA"]

BASE_ADDRESS = "https://botsin.space/"
USERNAME = "@botbot "
NASA_ADDRESS_IMAGES = "https://api.nasa.gov/planetary/apod?api_key=%s"
MAX_REQUESTS_PER_HOUR = 30
TOO_MANY_REQUESTS_MESSAGE = "You're making too many requests!"
FILE_TYPES = ('*.png', '*.jpeg')
GIF_MESSAGE = "This bot does not support GIF format files. You have either supplied a GIF or another incompatible file." \
              " Your file was deleted. Type \"formats\" to get a list of supported formats.\n\n"
JSON_ERROR_MESSAGE = "Decoding JSON has failed"
INVALID_COMMAND = "{} not recognised as a command.\n"
CROP_OUT_OF_RANGE = "\nYour {0} value is out of range; {1} is the maximum value, and must be > 0"
CROP_FAILURE_MESSAGE = "\nCrop failed. You didn't supply enough parameters!" \
                       "\nPlease supply integers in the format crop <int> <int> <int> <int>"
MAX_MESSAGE_LENGTH = 500
ROTATE_COMMAND = "rotate"
ROTATE_SIMPLE = "simple"
ROOT = Path(__file__).parent.parent
BASE_DIRECTORY = ROOT / "src"
INPUT_FOLDER = BASE_DIRECTORY / "input"
RESOURCES_FOLDER = BASE_DIRECTORY / "resources"
DAILY_IMAGE = str(BASE_DIRECTORY / "daily" / "image.jpeg")
HISTOGRAM_JPEG = (str(INPUT_FOLDER / "histogram-{}.jpeg"))
IMAGE_INPUT = str(INPUT_FOLDER / "{}")
PNG_OUTPUT = str(INPUT_FOLDER / "{}.png")
JPEG_OUTPUT = str(INPUT_FOLDER / "{}.jpeg")
OPERATION_SUCCESSFUL_MESSAGE = "{} \U00002705 \n"
OPERATION_FAILED_MESSAGE = "{} \U0000274C \n"
HELP_MESSAGE = "Hello! \n\nWelcome to @botbot, the image processing bot for Mastodon!" \
               "\nThe bot can perform simple (and not so simple) image transformations.\n" \
               "\nCommands:" \
               "\nHelp - get help" \
               "\nAbout - get information about your image(s)" \
               "\nDecolourise - returns a decolourised version of your image(s)" \
               "\nPreserve <colour> - preserve a colour channel" \
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
               "\nLandmarks - detects landmarks present in the image" \
               "\nObjects - detects objects in the image" \
               "\nProperties - detects labels that can be applied to the image" \
               "\nAppend - append two or more images together" \
               "\nPNG - convert your image(s) to PNG format" \
               "\nJPEG - convert your images to jpeg format\n"
SUPPORTED_FORMATS_MESSAGE = "Currently supported file upload formats: \n" \
                            "- JPEG\n- PNG\n\n"  # This is Mastodon's doing.
SET_OF_COMMANDS = {"help", "about", "decolourise", "preserve", "histogram", "rotate", "enhance", "border", "crop",
                   "brightness", "contrast", "colour", "mirror", "flip", "transparent", "negative", "sepia", "blur",
                   "blurred", "border", "png,", "bmp", "landmarks", "objects", "properties", "append"}
SET_OF_COLOURS = {"red", "green", "blue"}
NEGATIVE_RESPONSES = ["Hey, you're mean!", "Well, if that's how you feel...", "Hold your tongue!"]
POSITIVE_RESPONSES = ["Why thank you!", "Same to you :)!", "Aww, you say such nice things."]
NEUTRAL_RESPONSES = ["Sure.", "Ok..."]
