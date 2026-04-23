from .shared.missing import MISSING_POLICIES
from .shared.selectors import select_from_batch


class LoadImageSelectorBatch:
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
    FUNCTION = "select"
    CATEGORY = "image"

    def select(self, index: int = 0, image_missing: str = "None", mask_missing: str = "None", image=None, mask=None):
        return select_from_batch(
            image=image,
            mask=mask,
            index=index,
            image_missing=image_missing,
            mask_missing=mask_missing,
        )
