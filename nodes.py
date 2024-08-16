import os
import json
import pathlib
from PIL import Image
from comfy.utils import ProgressBar

from .logger import logger


CATEGORY_STRING = "💀 D00MYs"

IMAGES_TYPES = [".jpg", ".jpeg", ".png", ".webp"]
CONVERT_TO_TYPES = ["PNG", "JPEG", "GIF", "BMP", "TIFF", "WebP", "ICO"]
CONVERT_TO_TYPES_EXT = {
    "PNG": ".png", 
    "JPEG": ".jpg", 
    "GIF": ".gif", 
    "BMP": ".bmp", 
    "TIFF": ".tiff", 
    "WebP": ".webp", 
    "ICO": ".ico",
}
TEXT_FORMAT = ["text", "json"]


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


class D00MYsImagesConverter:
    def __init__(self):
        logger.debug("Init of D00MYsImagesToPNG")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "directory": ("STRING", {"default": "X://path/to/images"}),
                "output_directory": ("STRING", {"default": "X://path/to/output"}),
                "convert_to":  (CONVERT_TO_TYPES, ),
            },
        }
    
    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("LoadedImagesPaths", "ConvertedPaths", "TotalConverted")    
    FUNCTION = "convert_images"
    CATEGORY = CATEGORY_STRING
    
    @classmethod
    def IS_CHANGED(s, directory: str, output_directory: str, convert_to: str, **kwargs):
        if directory is None or output_directory is None:
            return "input"
        return False

    @classmethod
    def VALIDATE_INPUTS(s, directory: str, output_directory: str, convert_to: str, **kwargs):
        if directory is None and output_directory is None:
            return True
        return validate_load_images(directory)

    def convert_images(self, directory: str, output_directory: str, convert_to: str, **kwargs):
        converted_images_paths = list()
        images_paths = list_images_paths(directory)
        images_total = len(images_paths)
        pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)
        pbar = ProgressBar(images_total)
        logger.debug(f"Images to convert: {images_total}")
        for k, image_path in enumerate(images_paths):
            try:
                image_name = pathlib.Path(image_path).stem
                image = Image.open(image_path)
                ext = CONVERT_TO_TYPES_EXT[convert_to]
                save_path = f"{os.path.join(output_directory, image_name)}{ext}"
                logger.debug(f"Saving: {save_path}")
                # Resize to 256px square for ICO
                if convert_to == "ICO":
                    image = image.resize((256, 256), Image.ANTIALIAS)
                image.save(save_path, convert_to)
                converted_images_paths.append(save_path)
                image.close()
            except Exception as e:
                logger.error(f"An error occured during the convertion of image {image_path}: {e}")
            pbar.update_absolute(k, images_total)
        if pbar is not None:
            pbar.update_absolute(images_total, images_total)
        logger.info(f"Finished converting {images_total} images to PNG")
        return ("\n".join(images_paths), "\n".join(converted_images_paths), images_total)


################################ Text Nodes

class D00MYsShowString:
    def __init__(self):
        logger.debug("Init of D00MYsShowString")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_string": ("STRING", {"forceInput": True}),
                "format":  (TEXT_FORMAT, ),
                "split_lines": ("BOOLEAN", { "default": False }),
            }
        }
    
    OUTPUT_NODE = True
    FUNCTION = "show_string"
    CATEGORY = CATEGORY_STRING
    
    @classmethod
    def IS_CHANGED(s, input_string, format, split_lines, **kwargs):
        if input_string is None:
            return "input"
        return True

    @classmethod
    def VALIDATE_INPUTS(s, input_string, format, split_lines, **kwargs):
        return True

    def show_string(self, input_string, format, split_lines, **kwargs):
        logger.info(f"Format = {format}, split_lines = {split_lines}")
        input = input_string.split("\n") if split_lines else input_string
        if format == "json":
            print(json.dumps(input))
        else:
            print(input)
        return (input,)

#####################################################################

NODE_CLASS_MAPPINGS = {
    "Images_Converter|D00MYs": D00MYsImagesConverter,
    "Show_String|D00MYs": D00MYsShowString,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Images_Converter|D00MYs": "Images Converter",
    "Show_String|D00MYs": "Show String Value",
}
