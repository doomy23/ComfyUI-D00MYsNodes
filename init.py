import shutil

from .logger import logger
from .utils import get_ext_dir, get_comfy_dir

#################################################################### Installing JS

def install_js():
    logger.info(f"Installing JSPAINT")
    # Copy JsPaint before extensions folder
    shutil.copytree(get_ext_dir("jspaint"), get_comfy_dir("web/jspaint"), dirs_exist_ok=True)
