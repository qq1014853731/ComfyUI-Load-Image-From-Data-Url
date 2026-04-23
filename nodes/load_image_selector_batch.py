from .shared.selectors import select_from_batch


class LoadImageSelectorBatch:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "index": ("INT", {"default": 0, "min": -2147483648, "max": 2147483647, "step": 1}),
                "none_when_missing": ("BOOLEAN", {"default": True}),
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

    def select(self, index: int = 0, none_when_missing: bool = True, image=None, mask=None):
        return select_from_batch(
            image=image,
            mask=mask,
            index=index,
            none_when_missing=none_when_missing,
        )
