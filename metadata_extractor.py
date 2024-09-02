import os
import hashlib
import folder_paths
import re
from typing import List

# Taken from : https://github.com/alexopus/ComfyUI-Image-Saver/blob/main/utils.py


"""
Given the file path, finds a matching sha256 file, or creates one
based on the headers in the source file
"""
def get_sha256(file_path: str):
    file_no_ext = os.path.splitext(file_path)[0]
    hash_file = file_no_ext + ".sha256"

    if os.path.exists(hash_file):
        try:
            with open(hash_file, "r") as f:
                return f.read().strip()
        except OSError as e:
            print(f"ComfyUI-Image-Saver: Error reading existing hash file: {e}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    try:
        with open(hash_file, "w") as f:
            f.write(sha256_hash.hexdigest())
    except OSError as e:
        print(f"ComfyUI-Image-Saver: Error writing hash to {hash_file}: {e}")

    return sha256_hash.hexdigest()

"""
Represent the given embedding name as key as detected by civitAI
"""
def civitai_embedding_key_name(embedding: str):
    return f'embed:{embedding}'

"""
Represent the given lora name as key as detected by civitAI
NB: this should also work fine for Lycoris
"""
def civitai_lora_key_name(lora: str):
    return f'LORA:{lora}'

"""
Based on a embedding name, eg: EasyNegative, finds the path as known in comfy, including extension
"""
def full_embedding_path_for(embedding: str):
    matching_embedding = next((x for x in __list_embeddings() if x.startswith(embedding)), None)
    if matching_embedding == None:
        return None
    return folder_paths.get_full_path("embeddings", matching_embedding)

"""
Based on a lora name, e.g., 'epi_noise_offset2', finds the path as known in comfy, including extension.
"""
def full_lora_path_for(lora: str):
    # Find the position of the last dot
    last_dot_position = lora.rfind('.')
    # Get the extension including the dot
    extension = lora[last_dot_position:] if last_dot_position != -1 else ""
    # Check if the extension is supported, if not, add .safetensors
    if extension not in folder_paths.supported_pt_extensions:
        lora += ".safetensors"

    # Find the matching lora path
    matching_lora = next((x for x in __list_loras() if x.endswith(lora)), None)
    if matching_lora is None:
        return None
    return folder_paths.get_full_path("loras", matching_lora)

def __list_loras():
    return folder_paths.get_filename_list("loras")

def __list_embeddings():
    return folder_paths.get_filename_list("embeddings")


# Taken from : https://github.com/alexopus/ComfyUI-Image-Saver/blob/main/prompt_metadata_extractor.py

"""
Extracts Embeddings and Lora's from the given prompts
and allows asking for their sha's 
This module is based on civit's plugin and website implementations
The image saver node goes through the automatic flow, not comfy, on civit
see: https://github.com/civitai/sd_civitai_extension/blob/2008ba9126ddbb448f23267029b07e4610dffc15/scripts/gen_hashing.py
see: https://github.com/civitai/civitai/blob/d83262f401fb372c375e6222d8c2413fa221c2c5/src/utils/metadata/automatic.metadata
"""
class PromptMetadataExtractor:
    # Anything that follows embedding:<characters except , or whitespace
    EMBEDDING = r'embedding:([^,\s\(\)\:]+)'
    # Anything that follows <lora:NAME> with allowance for :weight, :weight.fractal or LBW
    LORA = r'<lora:([^>:]+)(?::[^>]+)?>'

    def __init__(self, prompts: List[str]):
        self.__embeddings = {}
        self.__loras = {}
        self.__perform(prompts)

    """
    Returns the embeddings used in the given prompts in a format as known by civitAI
    Example output: {"embed:EasyNegative": "66a7279a88", "embed:FastNegativeEmbedding": "687b669d82", "embed:ng_deepnegative_v1_75t": "54e7e4826d", "embed:imageSharpener": "fe5a4dfc4a"}
    """
    def get_embeddings(self):
        return self.__embeddings
        
    """
    Returns the lora's used in the given prompts in a format as known by civitAI
    Example output: {"LORA:epi_noiseoffset2": "81680c064e", "LORA:GoodHands-beta2": "ba43b0efee"}
    """
    def get_loras(self):
        return self.__loras

    # Private API
    def __perform(self, prompts):
        for prompt in prompts:
            embeddings = re.findall(self.EMBEDDING, prompt, re.IGNORECASE | re.MULTILINE)
            for embedding in embeddings:
                self.__extract_embedding_information(embedding)
            
            loras = re.findall(self.LORA, prompt, re.IGNORECASE | re.MULTILINE)
            for lora in loras:
                self.__extract_lora_information(lora)

    def __extract_embedding_information(self, embedding: str):
        embedding_name = civitai_embedding_key_name(embedding)
        embedding_path = full_embedding_path_for(embedding)
        if embedding_path == None:
            return
        sha = self.__get_shortened_sha(embedding_path)
        # Based on https://github.com/civitai/sd_civitai_extension/blob/2008ba9126ddbb448f23267029b07e4610dffc15/scripts/gen_hashing.py#L53
        self.__embeddings[embedding_name] = sha

    def __extract_lora_information(self, lora: str):
        lora_name = civitai_lora_key_name(lora)
        lora_path = full_lora_path_for(lora)
        if lora_path == None:
            return
        sha = self.__get_shortened_sha(lora_path)
        # Based on https://github.com/civitai/sd_civitai_extension/blob/2008ba9126ddbb448f23267029b07e4610dffc15/scripts/gen_hashing.py#L63
        self.__loras[lora_name] = sha
    
    def __get_shortened_sha(self, file_path: str):
       return get_sha256(file_path)[:10]
