from .shared.tensors import empty_comfy_tensors
from .utils import load_uri_to_tensors


class LoadImageFromURI:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "uri": ("STRING", {"multiline": True, "default": ""}),
                "timeout": ("INT", {"default": 0, "min": 0, "max": 600, "step": 1}),
                "max_download_bytes": (
                    "INT",
                    {"default": 0, "min": 0, "max": 2147483647, "step": 1048576},
                ),
                "allow_empty": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "BOOLEAN")
    RETURN_NAMES = ("image", "mask", "has_image")
    FUNCTION = "load_image_from_uri"
    CATEGORY = "image"

    def load_image_from_uri(
        self,
        uri: str,
        timeout: int = 0,
        max_download_bytes: int = 0,
        allow_empty: bool = False,
    ):
        if not isinstance(uri, str) or not uri.strip():
            if allow_empty:
                image_tensor, mask_tensor = empty_comfy_tensors()
                return image_tensor, mask_tensor, False
            raise ValueError("`uri` must be a non-empty string.")

        image_tensor, mask_tensor = load_uri_to_tensors(
            uri.strip(),
            timeout=timeout,
            max_download_bytes=max_download_bytes,
        )
        return image_tensor, mask_tensor, True
