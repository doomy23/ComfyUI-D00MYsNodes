import os
import json
import piexif
import piexif.helper
import time
from io import BytesIO
import base64
import pathlib
import uuid
import random
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import folder_paths
from comfy.utils import ProgressBar

from .logger import logger
from .utils import get_comfy_dir, validate_load_images, list_images_paths, pil2tensor, tensor2pil, IMAGES_TYPES
from .metadata_extractor import PromptMetadataExtractor, get_sha256


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
# Taken from : https://github.com/alexopus/ComfyUI-Image-Saver/blob/main/nodes.py
CIVITAI_SAMPLER_MAP = {
    'euler_ancestral': 'Euler a',
    'euler': 'Euler',
    'lms': 'LMS',
    'heun': 'Heun',
    'dpm_2': 'DPM2',
    'dpm_2_ancestral': 'DPM2 a',
    'dpmpp_2s_ancestral': 'DPM++ 2S a',
    'dpmpp_2m': 'DPM++ 2M',
    'dpmpp_sde': 'DPM++ SDE',
    'dpmpp_2m_sde': 'DPM++ 2M SDE',
    'dpmpp_3m_sde': 'DPM++ 3M SDE',
    'dpm_fast': 'DPM fast',
    'dpm_adaptive': 'DPM adaptive',
    'ddim': 'DDIM',
    'plms': 'PLMS',
    'uni_pc_bh2': 'UniPC',
    'uni_pc': 'UniPC',
    'lcm': 'LCM',
}

def handle_whitespace(string: str):
    return string.strip().replace("\n", " ").replace("\r", " ").replace("\t", " ")

def parse_checkpoint_name(ckpt_name):
    return os.path.basename(ckpt_name)

def parse_checkpoint_name_without_extension(ckpt_name):
    return os.path.splitext(parse_checkpoint_name(ckpt_name))[0]

def split_paths(paths: str):
    splited_paths_1 = paths.split(",")
    splited_paths_2 = paths.split("\n")
    return list(set(splited_paths_1 + splited_paths_2))

def load_image(path: str):
    with Image.open(path) as image:
        tensor = pil2tensor(image)
        return tensor

def load_images(paths: list):
    results = []
    for path in paths:
        if os.path.isfile(path):
            if pathlib.Path(path).suffix in IMAGES_TYPES:
                # Load image
                results.append(load_image(path))
            else:
                logger.error(f"Cannot load {path} because it's not a valid image type.")
        elif os.path.isdir(path):
            # Load all directory images
            images_paths = list_images_paths(path)
            for image_path in images_paths:
                results.append(load_image(image_path))
        else:
            logger.error(f"Cannot load {path} because it does not exist.")
    return results

def load_caption(path: str):
    image_path = pathlib.Path(path)
    image_name = image_path.stem
    image_dir = str(image_path.parent)
    image_ext = image_path.suffix
    search_for = [
        f"{os.path.join(image_dir, image_name)}.txt",
        f"{os.path.join(image_dir, image_name)}.caption",
        f"{os.path.join(image_dir, image_name)}{image_ext}.txt",
        f"{os.path.join(image_dir, image_name)}{image_ext}.caption",
    ]
    logger.debug(f"Search for: {search_for}")
    for search in search_for:
        if os.path.exists(search):
            logger.debug(f"Found: {search}")
            # Load caption
            with open(search, "r", encoding="UTF-8") as fp:
                return str(fp.read())
    # If None found return empty String
    return ""

def load_images_with_captions(paths: list):
    images = list()
    captions = list()
    for path in paths:
        if os.path.isfile(path):
            if pathlib.Path(path).suffix in IMAGES_TYPES:
                captions.append(load_caption(path))
                images.append(load_image(path))
            else:
                logger.error(f"Cannot load {path} because it's not a valid image type.")
        elif os.path.isdir(path):
            images_paths = list_images_paths(path)
            for image_path in images_paths:
                captions.append(load_caption(image_path))
                images.append(load_image(image_path))
        else:
            logger.error(f"Cannot load {path} because it does not exist.")
    return images, captions

def save_image(path, image_type, image: Image, exif_data=None, quality=100, optimize=True):
    if image_type == 'JPEG':
        image.save(path, image_type, quality=quality, optimize=optimize, dpi=image.info.get('dpi'))
    elif image_type == 'WebP':
        image.save(path, image_type, quality=quality, lossless=True, exif=exif_data)
    elif image_type == 'PNG':
        image.save(path, image_type, pnginfo=exif_data, optimize=optimize)
    elif image_type == 'BMP':
        image.save(path, image_type)
    elif image_type == 'TIFF':
        image.save(path, image_type, quality=quality, optimize=optimize)
    else:
        image.save(path, image_type, pnginfo=exif_data, optimize=optimize)

def extract_metadata(prompt_data, extra_pnginfo, img, file_type):
    metadata = None
    exif_bytes = None
    checkpoint = None
    steps = None
    sampler = None
    seed = None
    cfg = None
    positive = None
    negative = None
    embeddings = None
    loras = None
    text = {}
    # logger.info(f"prompt = {prompt_data}")
    for key in prompt_data.keys():
        node = prompt_data[key]
        if "inputs" in node.keys():
            for input_key in node["inputs"].keys():
                input = node["inputs"][input_key]
                if "text" == input_key:
                    if isinstance(input, list): 
                        id = input[0]
                        if id in text.keys():
                            text[key] = text[id]
                    else:
                        text[key] = input
                if "text2" == input_key:  # For Show Text outputs
                    text[key] = input
    # logger.info(f"{text}")
    for key in prompt_data.keys():
        node = prompt_data[key]
        logger.info(f"node {key} = {node}")
        if "inputs" in node.keys():
            for input_key in node["inputs"].keys():
                input = node["inputs"][input_key]
                try:
                    if "base_ckpt_name" in input_key and input != "None":
                        checkpoint = os.path.join(get_comfy_dir("models/checkpoints"), input)
                    if "steps" == input_key:
                        steps = input
                    if "seed" == input_key:
                        seed = input
                    if "cfg" == input_key:
                        cfg = input
                    if "sampler_name" == input_key:
                        sampler = CIVITAI_SAMPLER_MAP.get(input.replace("_gpu", "").replace("_cfg_pp", ""), None)
                    if "positive" == input_key:
                        # Check potential positive 
                        if isinstance(input, list): 
                            id = input[0]
                            if id in text.keys():
                                positive = text[id]
                    if "negative" == input_key:
                        # Check potential negative 
                        if isinstance(input, list): 
                            id = input[0]
                            if id in text.keys():
                                negative = text[id]
                except Exception as e:
                    logger.error(f"Don't know what to do with metadata {input}: {e}", e)
    if positive:
        negative = negative if negative else ""
        try:
            metadata_extractor = PromptMetadataExtractor([positive, negative])
            embeddings = metadata_extractor.get_embeddings()
            loras = metadata_extractor.get_loras()
        except Exception as e:
            logger.error(f"Error during metadata extraction: {e}", e)
    else:
        positive = ""
        negative = ""
        embeddings = {}
        loras = {}
    # Save the metadata
    logger.debug({
        "checkpoint": checkpoint,
        "steps": steps,
        "sampler": sampler,
        "seed": seed,
        "cfg": cfg,
        "positive": positive,
        "negative": negative,
        "embeddings": embeddings,
        "loras": loras
    })
    if checkpoint:
        modelhash = get_sha256(checkpoint)[:10]
    else:
        modelhash = ""
    extension_hashes = json.dumps(embeddings | loras | { "model": modelhash })
    basemodelname = parse_checkpoint_name_without_extension(checkpoint) if checkpoint else None
    positive_a111_params = handle_whitespace(positive)
    negative_a111_params = f"\nNegative prompt: {handle_whitespace(negative)}"
    width = img.width
    height = img.height
    step_str = f"Steps: {steps}" if steps else ""
    sampler_str = f"Sampler: {sampler}" if sampler else ""
    cfg_str = f"CFG scale: {cfg}" if cfg else ""
    seed_str = f"Seed: {seed}" if seed else ""
    size_str = f"Size: {width}x{height}"
    all_str = " ,".join([step_str, sampler_str, cfg_str, seed_str, size_str])
    a111_params = f"{positive_a111_params}{negative_a111_params}\n{all_str}, Model hash: {modelhash}, Model: {basemodelname}, Hashes: {extension_hashes}, Version: ComfyUI"
    if file_type == 'PNG':
        metadata = PngInfo()
        metadata.add_text("parameters", a111_params)
        if prompt_data is not None:
            metadata.add_text("prompt", json.dumps(prompt_data))
        if extra_pnginfo is not None:
            for x in extra_pnginfo:
                metadata.add_text(x, json.dumps(extra_pnginfo[x]))
    else:
        exif_bytes = piexif.dump({
            "Exif": {
                piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(a111_params, encoding="unicode")
            },
        })
    return metadata, exif_bytes


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
    RETURN_NAMES = ("Loaded Images Paths", "Converted Paths", "Total Converted")
    FUNCTION = "convert_images"
    CATEGORY = CATEGORY_STRING

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
                save_image(save_path, convert_to, image)
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
                "text": ("STRING", {"forceInput": True, "multiline": True}),
                "split_lines": ("BOOLEAN", {"default": False}),
            }
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "show_string"
    CATEGORY = CATEGORY_STRING
    
    def show_string(self, text, split_lines, **kwargs):
        result = list()
        split_lines = split_lines[0]
        for string in text:
            if split_lines:
                lines = string.split("\n")
                result += lines
            else:
                result.append(string)
        return {"ui": {"text": result}, "result": (result,)}
    

class D00MYsStringsFromList:
    def __init__(self):
        self.type = "output"
        logger.debug("Init of D00MYsStringFromList")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True, "multiline": True}),
                "index": ("INT", {"default": 0}),
                "length": ("INT", {"default": 1}),
            }
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "get_string"
    CATEGORY = CATEGORY_STRING

    def get_string(self, text: list, index, length, **kwargs):
        results = []
        try:
            if len(text) == 1:
                # Split it
                text = text[0].split("\n")
            results = text[int(index[0]):int(index[0])+int(length[0])]
        except Exception as e:
            logger.error(f"An error occured : {e}")
        return (results, )
    

class D00MYsSaveText:
    def __init__(self):
        logger.debug("Init of D00MYsSaveText")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True, "multiline": True}),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
            },
            "optional": {
                "images_paths": ("STRING", {"forceInput": True}),
            }
        }

    INPUT_IS_LIST = True    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("File Path",)
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (False,)
    FUNCTION = "save_file"
    CATEGORY = CATEGORY_STRING

    def save_file(self, text: list, filename_prefix: list, images_paths: list, **kwargs):
        filename_prefix = filename_prefix[0]
        path = None
        if len(images_paths) == 1:
            image_path = images_paths[0]
            if len(text) == 1:
                text = text[0]
            else:
                text = "\n".join(text)
            if image_path:
                image_path_obj = pathlib.Path(image_path)
                image_name = image_path_obj.stem
                image_dir = str(image_path_obj.parent)
                path = os.path.join(image_dir, f"{image_name}.txt")
            else:
                index = 1
                path = os.path.join(get_comfy_dir("output"), f"{filename_prefix}_{str(index).zfill(5)}_.txt")
                while os.path.exists(path):
                    index = index + 1
                    path = os.path.join(get_comfy_dir("output"), f"{filename_prefix}_{str(index).zfill(5)}_.txt")
            if path:
                with open(path, "w+", encoding="UTF-8") as fp:
                    fp.write(text)
                logger.info(f"Created file {path}")
        elif len(images_paths) == len(text):
            for index, image_path in enumerate(images_paths):
                text_to_save = text[index]
                image_path_obj = pathlib.Path(image_path)
                image_name = image_path_obj.stem
                image_dir = str(image_path_obj.parent)
                path = os.path.join(image_dir, f"{image_name}.txt")
                with open(path, "w+", encoding="UTF-8") as fp:
                    fp.write(text_to_save)
                logger.info(f"Created file {path}")
        else:
            logger.error(f"Text length must be the same as image paths or there must be only one image path. Got {len(images_paths)}.")
        return (path,)


################################ Images Nodes

class D00MYsSaveImage:
    def __init__(self):
        self.type = "output"
        logger.debug("Init of D00MYsSaveImage")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {"forceInput": True}),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "file_type":  (CONVERT_TO_TYPES, ),
                "save_metadata": ("BOOLEAN", {"default": True}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }
    
    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("Images Paths",)
    FUNCTION = "save_image"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (True,)
    CATEGORY = CATEGORY_STRING

    def save_image(self, images: list, filename_prefix: list, file_type: list, save_metadata: list, prompt, extra_pnginfo, **kwargs):
        filename_prefix = filename_prefix[0]
        file_type = file_type[0]
        save_metadata = save_metadata[0]
        results = list()
        results_paths = list()
        pbar = ProgressBar(len(images))
        for index, image in enumerate(images):
            try:
                img = tensor2pil(image)
                full_output_folder, filename, counter, subfolder, prefix = folder_paths.get_save_image_path(filename_prefix, get_comfy_dir("output"), 
                                                                                                            image.shape[1], image.shape[0])
                num = counter+index
                image_file_name = os.path.join(full_output_folder, f"{filename}_{str(num).zfill(5)}.png")
                while os.path.exists(image_file_name):  # Iterates until find a file number that does not exists
                    num = num+1
                    image_file_name = os.path.join(full_output_folder, f"{filename}_{str(num).zfill(5)}.png")
                logger.info(f"Saving {image_file_name}")
                # Resize to 256px square for ICO
                if file_type == "ICO":
                    img = img.resize((256, 256), Image.ANTIALIAS)
                metadata = None
                exif_bytes = None
                # Extract the metadata
                if save_metadata:
                    try:
                        metadata, exif_bytes = extract_metadata(prompt[0], extra_pnginfo[0], img, file_type)
                    except Exception as e:
                        logger.error(f"Cannot save image metadata: {e}", e)
                save_image(image_file_name, file_type, img, exif_data=metadata)
                if exif_bytes:
                    piexif.insert(exif_bytes, image_file_name)
                results.append({
                    "filename": os.path.basename(image_file_name),
                    "subfolder": subfolder,
                    "type": self.type
                })
                results_paths.append(image_file_name)
            except Exception as e:
                logger.error(f"Cannot save image {image_file_name}: {e}")
                raise e
            pbar.update_absolute(index+1, len(images))
        if pbar is not None:
            pbar.update_absolute(len(images), len(images))
        return {"ui": {"images": results}, "result": (results_paths,)}


class D00MYsRandomImages:
    def __init__(self):
        self.type = "output"
        logger.debug("Init of D00MYsRandomImages")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {"forceInput": True}),
                "count": ("INT", {"default": 1}),
            },
            "optional": {
                "captions": ("STRING", {"forceInput": True}),
            }
        }
    
    @classmethod
    def IS_CHANGED(s, images, count, captions, **kwargs):
        return time.time()
    
    INPUT_IS_LIST = True
    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("Images", "Captions",)
    FUNCTION = "random_images"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (True, True,)
    CATEGORY = CATEGORY_STRING

    def random_images(self, images: list, count: list, captions: list, **kwargs):
        count = count[0]
        if len(captions) == 0:
            result = random.choices(images, k=count)
            return (result, [],)
        else:
            choices = [(image, caption) for image, caption in zip(images, captions)]
            results = random.choices(choices, k=count)
            results_images = list()
            results_captions = list()
            for image, caption in results:
                results_images.append(image)
                results_captions.append(caption)
            return (results_images, results_captions,)


class D00MYsLoadImagesFromPaths:
    def __init__(self):
        self.type = "output"
        logger.debug("Init of D00MYsLoadImagesFromPath")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "paths": ("STRING", {"default": "X://path/to/images/image.ext"}),
                "load_captions": ("BOOLEAN", {"default": False}),
            }
        }
    
    @classmethod
    def IS_CHANGED(s, paths, load_captions, **kwargs):
        return time.time()
    
    INPUT_IS_LIST = True
    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("Images", "Captions")
    FUNCTION = "load_images"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (True, True,)
    CATEGORY = CATEGORY_STRING

    def load_images(self, paths: list, load_captions: list, **kwargs):
        load_captions = load_captions[0]
        if len(paths) == 1:
            # Split it
            paths = split_paths(paths[0])
        logger.debug(f"Load captions? {load_captions}, Paths = {paths}")
        if load_captions:
            # Load .txt or .caption files matching with its image
            images, captions = load_images_with_captions(paths)
            return (images, captions,)
        else:
            return (load_images(paths), [],)


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
    
    @classmethod
    def IS_CHANGED(s, image, **kwargs):
        return image
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("Image",)
    OUTPUT_NODE = True
    FUNCTION = "save_png"
    CATEGORY = CATEGORY_STRING

    def save_png(self, image: str, **kwargs):
        try:
            # Save in temp folder
            image_bs64 = image.split("data:image/png;base64,")[-1]
            image_pil = Image.open(BytesIO(base64.b64decode(f"{image_bs64}==")), formats=["PNG"]).convert('RGB')
            filepath = f"{get_comfy_dir('temp')}/JSPAINT_{uuid.uuid4()}.png"
            logger.info(f"Saving {filepath}")
            image_pil.save(filepath, "PNG")
            image_pil.close()
            return (load_image(filepath), )
        except Exception as e:
            logger.error(f"Cannot decode PNG file: {e}")
            return (None, )


#####################################################################

NODE_CLASS_MAPPINGS = {
    "Images_Converter|D00MYs": D00MYsImagesConverter,
    "Show_Text|D00MYs": D00MYsShowText,
    "Strings_From_List|D00MYs": D00MYsStringsFromList,
    "Save_Text|D00MYs": D00MYsSaveText,
    "Save_Images|D00MYs": D00MYsSaveImage,
    "Random_Images|D00MYs": D00MYsRandomImages,
    "Load_Images_From_Paths|D00MYs": D00MYsLoadImagesFromPaths,
    "JSPaint|D00MYs": D00MYsJSPaint,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Images_Converter|D00MYs": "🔷 Images Converter",
    "Show_Text|D00MYs": "📃 Show Text Value",
    "Strings_From_List|D00MYs": "📎 Strings from List",
    "Save_Text|D00MYs": "💾 Save Text",
    "Save_Images|D00MYs": "🖼️ Save Images",
    "Random_Images|D00MYs": "🔀 Random Images",
    "Load_Images_From_Paths|D00MYs": "📁 Load Images from Paths",
    "JSPaint|D00MYs": "✏️ JSPaint Node",
}
