from .batch_load_image_selector_node import BatchLoadImageSelector


class LoadImageSelectorList(BatchLoadImageSelector):
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
    INPUT_IS_LIST = True
    FUNCTION = "select"
    CATEGORY = "image"

    @staticmethod
    def _first_control_value(value, default=None):
        if isinstance(value, (list, tuple)):
            return value[0] if value else default
        return value

    def select(self, index: int = 0, none_when_missing: bool = True, image=None, mask=None):
        index = self._first_control_value(index, 0)
        none_when_missing = bool(self._first_control_value(none_when_missing, True))

        if image is None and mask is None:
            raise ValueError("At least one input is required: connect `image`, `mask`, or both.")

        if image is None:
            image = [self._empty_image_like(mask_tensor) for mask_tensor in mask]
        if mask is None:
            mask = [self._empty_mask_like(image_tensor) for image_tensor in image]

        if len(image) != len(mask):
            raise ValueError(f"Image/mask list length mismatch: {len(image)} images, {len(mask)} masks.")

        selected_index = self._normalize_index(index, len(image))
        if selected_index is None:
            if none_when_missing:
                empty_image, empty_mask = self.empty_comfy_tensors()
                return (empty_image, empty_mask, False)
            raise ValueError(
                f"Index out of range: index={index}, valid range is [0, {len(image) - 1}] or negative equivalent."
            )

        selected_image = image[selected_index]
        selected_mask = mask[selected_index]
        has_image = not self._is_placeholder(selected_image, selected_mask)

        if not has_image and not none_when_missing:
            raise ValueError("Selected image is empty placeholder while `none_when_missing` is False.")

        return (selected_image, selected_mask, has_image)
