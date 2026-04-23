from .shared.missing import MISSING_POLICIES
from .shared.selectors import select_from_list


def unwrap_list_input(value, default):
    if value is None:
        return default
    if isinstance(value, list):
        return value[0]
    return value


class LoadImageSelectorList:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "index": ("INT", {"default": 0, "min": -2147483648, "max": 2147483647, "step": 1}),
                "image_missing": (list(MISSING_POLICIES), {"default": "None"}),
                "mask_missing": (list(MISSING_POLICIES), {"default": "None"}),
            },
            "optional": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "BOOLEAN")
    RETURN_NAMES = ("image", "mask", "has_image")
    INPUT_IS_LIST = True
    FUNCTION = "select"
    CATEGORY = "image"

    def select(self, index=None, image_missing=None, mask_missing=None, image=None, mask=None):
        return select_from_list(
            images=image,
            masks=mask,
            index=unwrap_list_input(index, 0),
            image_missing=unwrap_list_input(image_missing, "None"),
            mask_missing=unwrap_list_input(mask_missing, "None"),
        )
