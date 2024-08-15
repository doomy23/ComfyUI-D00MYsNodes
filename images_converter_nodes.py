import os
import pathlib
from PIL import Image
from comfy.utils import ProgressBar

from .logger import logger


IMAGES_TYPES = [".jpg", ".jpeg", ".png", ".webp"]


def validate_load_images(directory: str):
    if not os.path.isdir(directory):
            return f"Directory '{directory}' cannot be found."
    files = os.listdir(directory)
    if len(files) == 0:
        return f"No files in directory '{directory}'."
    return True

def list_images_paths(directory: str):
    try:
        files_paths = [os.path.join(directory, file) for file in os.listdir(directory)]
        images_paths = list(filter(lambda file_path: os.path.isfile(file_path) and pathlib.Path(file_path).suffix in IMAGES_TYPES, files_paths))
        return images_paths
    except Exception as e:
        return []


################################ Coverter Nodes


class ImagesToPNG:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "directory": ("STRING", {"default": "X://path/to/images"}),
                "output_directory": ("STRING", {"default": "X://path/to/output"}),
            },
        }
    
    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("LoadedImagesPaths", "ConvertedPaths", "TotalConverted")    
    FUNCTION = "convert_images_to_png"
    CATEGORY = "💀 D00MYs/Converter"
    
    @classmethod
    def IS_CHANGED(s, directory: str, **kwargs):
        if directory is None:
            return "input"
        return False

    @classmethod
    def VALIDATE_INPUTS(s, directory: str, **kwargs):
        if directory is None:
            return True
        return validate_load_images(directory)

    def convert_images_to_png(self, directory: str, output_directory: str, **kwargs):
        images_paths = list_images_paths(directory)
        images_total = len(images_paths)
        pbar = ProgressBar(images_total)
        logger.debug(f"Images to convert ({images_total}):\n{', '.join(images_paths)}")
        for k, image_path in enumerate(images_paths):
            try:
                image = Image.open(image_path)
            except Exception as e:
                logger.error(f"An error occured during the convertion of image {image_path}: {e}")
            pbar.update_absolute(k, images_total)
        if pbar is not None:
            pbar.update_absolute(images_total, images_total)
        logger.info(f"Finished converting {images_total} images to PNG")
        return ("", "", images_total)


NODE_CLASS_MAPPINGS = {
    "ImagesToPNG": ImagesToPNG,
}