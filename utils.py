import os
import inspect
from server import PromptServer

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
