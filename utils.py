import os
import inspect
import torch
import numpy
import pathlib
from PIL import Image
from server import PromptServer

IMAGES_TYPES = [".jpg", ".jpeg", ".png", ".webp"]

# https://github.com/pythongosssss/ComfyUI-Custom-Scripts/blob/main/pysssss.py
def get_ext_dir(subpath=None, mkdir=False):
    dir = os.path.dirname(__file__)
    if subpath is not None:
        dir = os.path.join(dir, subpath)

    dir = os.path.abspath(dir)

    if mkdir and not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def get_comfy_dir(subpath=None, mkdir=False):
    dir = os.path.dirname(inspect.getfile(PromptServer))
    if subpath is not None:
        dir = os.path.join(dir, subpath)

    dir = os.path.abspath(dir)

    if mkdir and not os.path.exists(dir):
        os.makedirs(dir)
    return dir

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
    
# Stolen from : https://github.com/GeekyGhost/ComfyUI-GeekyRemB/blob/SketchUITest/scripts/GeekyRembv2.py
def pil2tensor(image):
    np_image = numpy.array(image).astype(numpy.float32) / 255.0
    if np_image.ndim == 2:  # If it's a grayscale image (mask)
        np_image = np_image[None, None, ...]  # Add batch and channel dimensions
    elif np_image.ndim == 3:  # If it's an RGB image
        np_image = np_image[None, ...]  # Add batch dimension
    return torch.from_numpy(np_image)

def tensor2pil(tensor):
    tensor = tensor2numpy(tensor)
    if numpy.ndim(tensor)>3:
        assert tensor.shape[0] == 1
        tensor = tensor[0]
    return Image.fromarray(tensor)

def tensor2numpy(tensor):
    tensor = tensor*255
    return numpy.array(tensor, dtype=numpy.uint8)