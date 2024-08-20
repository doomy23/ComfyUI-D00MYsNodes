import os
import shutil
import inspect
from server import PromptServer

from .logger import logger

#################################################################### Installing JS
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

def get_web_ext_dir():
    dir = get_comfy_dir("web/extensions/D00MYs")
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def install_js():
    src_dir = get_ext_dir("web/js")
    if not os.path.exists(src_dir):
        logger.error("NO JS!")
        return
    dst_dir = get_web_ext_dir()
    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
