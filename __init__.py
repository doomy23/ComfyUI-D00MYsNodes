from .images_converter_nodes import ImagesToPNG
from .text_nodes import ShowString

from .logger import logger

NODE_CLASS_MAPPINGS = {
    "ImagesToPNG": ImagesToPNG,
    "ShowString": ShowString,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImagesToPNG": "Images to PNG converter",
    "ShowString": "Show String",
}

logger.info("Loading D00MYs...")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]