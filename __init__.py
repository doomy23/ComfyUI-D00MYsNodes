from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from .logger import logger
from .init import install_js

logger.info(f"Loading D00MYs nodes: {NODE_CLASS_MAPPINGS}")
install_js()

WEB_DIRECTORY = "./web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
