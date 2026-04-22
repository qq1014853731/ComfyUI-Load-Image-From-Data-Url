import torch

from .utils import ImageNodeUtils


class BatchLoadImageSelector(ImageNodeUtils):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "index": ("INT", {"default": 0, "min": -2147483648, "max": 2147483647, "step": 1}),
                "none_when_missing": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "BOOLEAN")
    RETURN_NAMES = ("image", "mask", "has_image")
    FUNCTION = "select"
    CATEGORY = "image"

    @staticmethod
    def _is_placeholder(image_tensor: torch.Tensor, mask_tensor: torch.Tensor) -> bool:
        return (
            tuple(image_tensor.shape) == (1, 1, 1, 3)
            and tuple(mask_tensor.shape) == (1, 1, 1)
            and bool(torch.all(image_tensor == 0).item())
            and bool(torch.all(mask_tensor == 1).item())
        )

    def select(self, image: torch.Tensor, mask: torch.Tensor, index: int = 0, none_when_missing: bool = True):
        if image.ndim != 4 or mask.ndim != 3:
            raise ValueError("Invalid batch tensor shape for `image` or `mask`.")

        batch_size = int(image.shape[0])
        if batch_size <= 0:
            if none_when_missing:
                empty_image, empty_mask = self.empty_comfy_tensors()
                return (empty_image, empty_mask, False)
            raise ValueError("Image batch is empty.")

        selected_index = int(index)
        if selected_index < 0:
            selected_index += batch_size

        if selected_index < 0 or selected_index >= batch_size:
            if none_when_missing:
                empty_image, empty_mask = self.empty_comfy_tensors()
                return (empty_image, empty_mask, False)
            raise ValueError(
                f"Index out of range: index={index}, valid range is [0, {batch_size - 1}] or negative equivalent."
            )

        selected_image = image[selected_index : selected_index + 1]
        selected_mask = mask[selected_index : selected_index + 1]
        has_image = not self._is_placeholder(selected_image, selected_mask)

        if not has_image and not none_when_missing:
            raise ValueError("Selected image is empty placeholder while `none_when_missing` is False.")

        return (selected_image, selected_mask, has_image)
