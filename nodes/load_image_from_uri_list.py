from .shared.dynamic_inputs import ContainsAnyDict, collect_uri_list
from .shared.missing import MISSING_POLICIES, validate_missing_policy
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
                "uri_missing": (list(MISSING_POLICIES), {"default": "None"}),
            },
            # uri_1, uri_2, ... are created by the frontend extension at runtime.
            "optional": ContainsAnyDict(),
        }

    RETURN_TYPES = ("IMAGE", "MASK", "BOOLEAN", "INT")
    RETURN_NAMES = ("image", "mask", "has_image", "count")
    OUTPUT_IS_LIST = (True, True, False, False)
    FUNCTION = "load_images_from_uri_list"
    CATEGORY = "lifu/image"

    def load_images_from_uri_list(
        self,
        timeout: int = 0,
        max_download_bytes: int = 0,
        uri_missing: str = "None",
        **kwargs,
    ):
        validate_missing_policy(uri_missing, "uri_missing")
        uri_list = collect_uri_list(kwargs)

        if not uri_list:
            return [], [], False, 0

        image_tensors = []
        mask_tensors = []
        real_image_count = 0
        for uri in uri_list:
            if not uri:
                if uri_missing == "None":
                    image_tensors.append(None)
                    mask_tensors.append(None)
                    continue
                if uri_missing == "Throw error":
                    raise ValueError("URI list contains an empty URI item.")
                image_tensor, mask_tensor = empty_comfy_tensors()
                image_tensors.append(image_tensor)
                mask_tensors.append(mask_tensor)
                continue

            image_tensor, mask_tensor = load_uri_to_tensors(
                uri,
                timeout=timeout,
                max_download_bytes=max_download_bytes,
            )
            image_tensors.append(image_tensor)
            mask_tensors.append(mask_tensor)
            real_image_count += 1

        return image_tensors, mask_tensors, real_image_count > 0, len(uri_list)
