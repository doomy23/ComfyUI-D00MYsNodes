import os
from io import BytesIO
import base64
import pathlib
import uuid
import torchvision
from PIL import Image
from comfy.utils import ProgressBar

from .logger import logger
from .utils import get_comfy_dir, validate_load_images, list_images_paths, pil2tensor, IMAGES_TYPES


CATEGORY_STRING = "💀 D00MYs"
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

def split_paths(paths: str):
    splited_paths_1 = paths.split(",")
    splited_paths_2 = paths.split("\n")
    return list(set(splited_paths_1 + splited_paths_2))

def load_images(paths: list):
    results = []
    for path in paths:
        if os.path.isfile(path):
            if pathlib.Path(path).suffix in IMAGES_TYPES:
                # Load image
                image_temp = Image.open(path, mode="r")
                image_tensor = pil2tensor(image_temp)
                results.append(image_tensor)
            else:
                logger.error(f"Cannot load {path} because it's not a valid image type.")
        else:
            logger.error(f"Cannot load {path} because it does not exist.")
    return results

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
        return True  # Always restart unless told not to

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

class D00MYsShowText:
    def __init__(self):
        self.type = "output"
        logger.debug("Init of D00MYsShowText")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
                "split_lines": ("BOOLEAN", { "default": False }),
            }
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "show_string"
    CATEGORY = CATEGORY_STRING
    
    def show_string(self, text, split_lines, **kwargs):
        result = list()
        for t, sl in zip(text, split_lines):
            if sl == True:
                if isinstance(t, list):
                    input = list()
                    for text_el in t:
                        input += text_el.split("\n")
                else:
                    input = t.split("\n")
                result += input
            else:
                result += t if isinstance(t, list) else [t]
        return {"ui": {"text": result}, "result": (result,)}
    

class D00MYsLoadImagesFromPaths:
    def __init__(self):
        self.type = "output"
        logger.debug("Init of D00MYsLoadImagesFromPath")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "paths": ("STRING", {"default": "X://path/to/images/image.ext"}),
            }
        }
    
    INPUT_IS_LIST = True
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "load_images"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (True,)
    CATEGORY = CATEGORY_STRING

    def load_images(self, paths, **kwargs):
        if isinstance(paths, list):
            if len(paths) == 1:
                # Split it
                paths = split_paths(paths[0])
            return (load_images(paths),)
        else:
            return (load_images(split_paths(paths)),)


################################ JSPaint Nodes

class D00MYsJSPaint:
    def __init__(self):
        self.type = "output"
        logger.debug("Init of D00MYsJSPaint")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "optional": {},
            "required": {
                "image": ("JSPAINT", {"default": None},),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }
    
    RETURN_TYPES = ("IMAGE",)
    OUTPUT_NODE = True
    FUNCTION = "save_png"
    CATEGORY = CATEGORY_STRING

    def save_png(self, image: str, **kwargs):
        try:
            # Save in temp folder
            image_bs64 = image.split("data:image/png;base64,")[-1]
            image_pil = Image.open(BytesIO(base64.b64decode(f"{image_bs64}==")), mode="r", formats=["PNG"]).convert('RGB')
            filepath = f"{get_comfy_dir('temp')}/JSPAINT_{uuid.uuid4()}.png"
            logger.info(f"Saving {filepath}")
            image_pil.save(filepath, "PNG")
            image_pil.close()
            # Load from temp folder as tensor
            image_temp = Image.open(filepath, mode="r")
            image_tensor = pil2tensor(image_temp)
            return (image_tensor, )
        except Exception as e:
            logger.error(f"Cannot decode PNG file: {e}")
            return (None, )


#####################################################################

NODE_CLASS_MAPPINGS = {
    "Images_Converter|D00MYs": D00MYsImagesConverter,
    "Show_Text|D00MYs": D00MYsShowText,
    "JSPaint|D00MYs": D00MYsJSPaint,
    "Load_Images_From_Paths|D00MYs": D00MYsLoadImagesFromPaths,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Images_Converter|D00MYs": "🔷 Images Converter",
    "Show_Text|D00MYs": "📃 Show Text Value",
    "JSPaint|D00MYs": "✏️ JSPaint Node",
    "Load_Images_From_Paths|D00MYs": "📁 Load Images from Paths",
}
