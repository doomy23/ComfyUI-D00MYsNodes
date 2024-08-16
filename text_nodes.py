from .logger import logger

################################ Text Nodes

class D00MYsShowString:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_string": ("STRING", {"forceInput": True})
            }
        }
    
    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING")
    RETURN_NAMES = ("String")    
    FUNCTION = "show"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (True,)
    CATEGORY = "💀 D00MYs/Text"
    
    @classmethod
    def IS_CHANGED(s, input_string, **kwargs):
        return True

    @classmethod
    def VALIDATE_INPUTS(s, input_string,  **kwargs):
        if input_string is None:
            return "input"
        return True

    def show(self, input_string, **kwargs):
        logger.info(f"String value = {input_string}")
        return input_string
