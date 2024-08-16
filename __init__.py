from .images_converter_nodes import ImagesToPNG
from .text_nodes import ShowString

NODE_CLASS_MAPPINGS = {
    "ImagesToPNG": ImagesToPNG,
    "ShowString": ShowString
}

__all__ = ["NODE_CLASS_MAPPINGS"]