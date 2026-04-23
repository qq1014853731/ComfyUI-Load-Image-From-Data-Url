from .shared.batch import cat_image_mask_batch, normalize_batch_tensor_sizes
from .shared.dynamic_inputs import ContainsAnyDict, collect_uri_list
from .shared.missing import MISSING_POLICIES, validate_missing_policy
from .shared.tensors import empty_comfy_tensors
from .utils import load_uri_to_tensors


class LoadImageFromURIBatch:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "timeout": ("INT", {"default": 0, "min": 0, "max": 600, "step": 1}),
                "max_download_bytes": (
                    "INT",
                    {"default": 0, "min": 0, "max": 2147483647, "step": 1048576},
                ),
                "size_mode": (
                    ["pad_to_max", "resize_to_first", "error"],
                    {"default": "pad_to_max"},
                ),
                "uri_missing": (list(MISSING_POLICIES), {"default": "None"}),
            },
            # uri_1, uri_2, ... are created by the frontend extension at runtime.
            "optional": ContainsAnyDict(),
        }

    RETURN_TYPES = ("IMAGE", "MASK", "BOOLEAN", "INT")
    RETURN_NAMES = ("image", "mask", "has_image", "count")
    FUNCTION = "load_images_from_uri_batch"
    CATEGORY = "image"

    def load_images_from_uri_batch(
        self,
        timeout: int = 0,
        max_download_bytes: int = 0,
        size_mode: str = "pad_to_max",
        uri_missing: str = "None",
        **kwargs,
    ):
        validate_missing_policy(uri_missing, "uri_missing")
        uri_list = collect_uri_list(kwargs)

        if not uri_list:
            return None, None, False, 0

        image_tensors = []
        mask_tensors = []
        real_image_count = 0
        for uri in uri_list:
            if not uri:
                if uri_missing == "None":
                    continue
                if uri_missing == "Throw error":
                    raise ValueError("URI batch contains an empty URI item.")
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

        if not image_tensors:
            return None, None, False, 0

        image_tensors, mask_tensors = normalize_batch_tensor_sizes(
            image_tensors,
            mask_tensors,
            size_mode=size_mode,
        )
        batch_image, batch_mask = cat_image_mask_batch(image_tensors, mask_tensors)
        return batch_image, batch_mask, real_image_count > 0, len(image_tensors)
