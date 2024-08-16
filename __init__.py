from .nodes import D00MYsImagesConverter, D00MYsShowString
from .logger import logger

NODE_CLASS_MAPPINGS = {
    "D00MYs_Images_Converter": D00MYsImagesConverter,
    "D00MYs_Show_String": D00MYsShowString,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "D00MYs_Images_Converter": "Images Converter",
    "D00MYs_Show_String": "Show String Value",
}

logger.info(f"Loading D00MYs nodes: {NODE_CLASS_MAPPINGS}")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
