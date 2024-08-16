
################################ Text Nodes

class ShowString:
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
    RETURN_NAMES = ()    
    FUNCTION = "show"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (True,)
    CATEGORY = "💀 D00MYs/Text"
    
    @classmethod
    def IS_CHANGED(s, input_string, **kwargs):
        return True

    @classmethod
    def VALIDATE_INPUTS(s, input_string,  **kwargs):
        return True

    def show(self, input_string, **kwargs):
        return input_string
