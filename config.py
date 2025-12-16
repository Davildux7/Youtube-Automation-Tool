import os
import PIL.Image
from dotenv import load_dotenv

def setup_config():
    # load .env
    load_dotenv()

    # fix for newer pillow versions bc why not
    if not hasattr(PIL.Image, 'ANTIALIAS'):
        PIL.Image.ANTIALIAS = PIL.Image.LANCZOS # type: ignore

WATERMARK_FILENAME = "watermark.png"

# run everything when imported
setup_config()