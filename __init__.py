from .images_converter_nodes import ImagesToPNG
from .text_nodes import ShowString

from .logger import logger

NODE_CLASS_MAPPINGS = {
    "Images_to_PNG": ImagesToPNG,
    "Show_String": ShowString,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Images_to_PNG": "Images to PNG converter",
    "Show_String": "Show String",
}

logger.info("Loading D00MYs...")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]