from .shared.dynamic_inputs import ContainsAnyDict, collect_uri_list
from .shared.tensors import empty_comfy_tensors
from .utils import load_uri_to_tensors


class LoadImageFromURIList:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "timeout": ("INT", {"default": 0, "min": 0, "max": 600, "step": 1}),
                "max_download_bytes": (
                    "INT",
                    {"default": 0, "min": 0, "max": 2147483647, "step": 1048576},
                ),
                "allow_empty": ("BOOLEAN", {"default": False}),
            },
            # uri_1, uri_2, ... are created by the frontend extension at runtime.
            "optional": ContainsAnyDict(),
        }

    RETURN_TYPES = ("IMAGE", "MASK", "BOOLEAN", "INT")
    RETURN_NAMES = ("image", "mask", "has_image", "count")
    OUTPUT_IS_LIST = (True, True, False, False)
    FUNCTION = "load_images_from_uri_list"
    CATEGORY = "image"

    def load_images_from_uri_list(
        self,
        timeout: int = 0,
        max_download_bytes: int = 0,
        allow_empty: bool = False,
        **kwargs,
    ):
        uri_list = collect_uri_list(kwargs)

        if not uri_list:
            if allow_empty:
                image_tensor, mask_tensor = empty_comfy_tensors()
                return [image_tensor], [mask_tensor], False, 0
            raise ValueError("URI list is empty. Add at least one non-empty URI item.")

        image_tensors = []
        mask_tensors = []
        for uri in uri_list:
            image_tensor, mask_tensor = load_uri_to_tensors(
                uri,
                timeout=timeout,
                max_download_bytes=max_download_bytes,
            )
            image_tensors.append(image_tensor)
            mask_tensors.append(mask_tensor)

        return image_tensors, mask_tensors, True, len(uri_list)
