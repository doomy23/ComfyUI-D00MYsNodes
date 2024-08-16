from .images_converter_nodes import D00MYsImagesToPNG
from .text_nodes import D00MYsShowString

from .logger import logger

NODE_CLASS_MAPPINGS = {
    "D00MYs_Images_to_PNG": D00MYsImagesToPNG,
    "D00MYs_Show_String": D00MYsShowString,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "D00MYs_Images_to_PNG": "Images to PNG converter",
    "D00MYs_Show_String": "Show String",
}

logger.info("Loading D00MYs nodes...")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]