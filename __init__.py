from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from .logger import logger
from .init import install_js

nodesstr = "\n".join(NODE_CLASS_MAPPINGS.keys())
logger.info(f"Loading D00MYs nodes: {nodesstr}")
install_js()

WEB_DIRECTORY = "./web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
