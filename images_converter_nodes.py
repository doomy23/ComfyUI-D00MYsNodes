import os
import pathlib
from PIL import Image
from comfy.utils import ProgressBar

from .logger import logger

IMAGES_TYPES = [".jpg", ".jpeg", ".png", ".webp"]

def validate_load_images(directory: str):
    if not os.path.isdir(directory):
            return f"Directory '{directory}' cannot be found."
    dir_files = os.listdir(directory)
    if len(dir_files) == 0:
        return f"No files in directory '{directory}'."
    return True

def list_images_paths(directory: str):
    try:
        files = os.listdir(directory)
        images_paths = [os.path.join(directory, file) for file in files if not file.startswith(".") and 
                    os.path.isfile(file) and 
                    pathlib.Path(file).suffix in IMAGES_TYPES]
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

    def convert_images_to_png(self, directory: str, **kwargs):
        images_paths = self.list_images_paths(directory)
        images_total = len(images_paths)
        pbar = ProgressBar(images_total)

        logger.info(f"Images to convert ({images_total}):\n{images_paths.join("\n")}")

        if pbar is not None:
            pbar.update_absolute(images_total, images_total)

        return "", "", images_total


NODE_CLASS_MAPPINGS = {
    "ImagesToPNG": ImagesToPNG,
}