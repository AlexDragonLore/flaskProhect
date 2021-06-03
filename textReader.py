import pytesseract
from PIL import Image


def readText(file):
    image = Image.open(file)
    return pytesseract.image_to_string(image, config='-l rus')