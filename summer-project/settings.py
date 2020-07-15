from pathlib import Path

BASE_ADDRESS = "https://hostux.social/"
NASA_ADDRESS_IMAGES = "https://api.nasa.gov/planetary/apod?api_key=%s"
MAX_MESSAGE_LENGTH = 500
ROTATE_COMMAND = "rotate"
ROTATE_SIMPLE = "simple"
INPUT_FOLDER = Path("pix2pix/val/")
OUTPUT_FOLDER = Path("pix2pix/test/images/")
JPEG_INPUT = str(INPUT_FOLDER / "{}.jpeg")
JPEG_OUTPUT = str(OUTPUT_FOLDER / "{}.jpeg")
