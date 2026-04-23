import torch

from .utils import ImageNodeUtils


class LoadImageSelectorBatch(ImageNodeUtils):
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

    @staticmethod
    def _is_placeholder(image_tensor: torch.Tensor, mask_tensor: torch.Tensor) -> bool:
        return (
            tuple(image_tensor.shape) == (1, 1, 1, 3)
            and tuple(mask_tensor.shape) == (1, 1, 1)
            and bool(torch.all(image_tensor == 0).item())
            and bool(torch.all(mask_tensor == 1).item())
        )

    @staticmethod
    def _empty_mask_like(image_tensor: torch.Tensor) -> torch.Tensor:
        return torch.zeros(
            (int(image_tensor.shape[0]), int(image_tensor.shape[1]), int(image_tensor.shape[2])),
            dtype=image_tensor.dtype,
            device=image_tensor.device,
        )

    @staticmethod
    def _empty_image_like(mask_tensor: torch.Tensor) -> torch.Tensor:
        return torch.zeros(
            (int(mask_tensor.shape[0]), int(mask_tensor.shape[1]), int(mask_tensor.shape[2]), 3),
            dtype=mask_tensor.dtype,
            device=mask_tensor.device,
        )

    @staticmethod
    def _normalize_index(index: int, count: int):
        selected_index = int(index)
        if selected_index < 0:
            selected_index += count
        if selected_index < 0 or selected_index >= count:
            return None
        return selected_index

    def select(self, index: int = 0, none_when_missing: bool = True, image=None, mask=None):
        if image is None and mask is None:
            raise ValueError("At least one input is required: connect `image`, `mask`, or both.")

        if image is None:
            image = self._empty_image_like(mask)
        if mask is None:
            mask = self._empty_mask_like(image)

        if image.ndim != 4 or mask.ndim != 3:
            raise ValueError("Invalid batch tensor shape for `image` or `mask`.")

        batch_size = int(image.shape[0])
        if batch_size <= 0:
            if none_when_missing:
                empty_image, empty_mask = self.empty_comfy_tensors()
                return (empty_image, empty_mask, False)
            raise ValueError("Image batch is empty.")

        selected_index = self._normalize_index(index, batch_size)
        if selected_index is None:
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
