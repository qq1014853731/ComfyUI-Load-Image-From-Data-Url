import torch

from .utils import ImageNodeUtils


class BatchLoadImageSelector(ImageNodeUtils):
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

    @staticmethod
    def _is_list_input(value) -> bool:
        return isinstance(value, (list, tuple))

    @staticmethod
    def _empty_mask_like(image_tensor: torch.Tensor) -> torch.Tensor:
        kwargs = {"dtype": image_tensor.dtype}
        if hasattr(image_tensor, "device"):
            kwargs["device"] = image_tensor.device
        return torch.zeros((int(image_tensor.shape[0]), int(image_tensor.shape[1]), int(image_tensor.shape[2])), **kwargs)

    @staticmethod
    def _empty_image_like(mask_tensor: torch.Tensor) -> torch.Tensor:
        kwargs = {"dtype": mask_tensor.dtype}
        if hasattr(mask_tensor, "device"):
            kwargs["device"] = mask_tensor.device
        return torch.zeros(
            (int(mask_tensor.shape[0]), int(mask_tensor.shape[1]), int(mask_tensor.shape[2]), 3),
            **kwargs,
        )

    def _fill_missing_list_pair(self, images, masks):
        if images is None and masks is None:
            raise ValueError("At least one input is required: connect `image`, `mask`, or both.")

        if images is None:
            if not self._is_list_input(masks):
                raise ValueError("When only `mask` is connected, mask input must be a list or tensor.")
            return [self._empty_image_like(mask) for mask in masks], masks

        if masks is None:
            if not self._is_list_input(images):
                raise ValueError("When only `image` is connected, image input must be a list or tensor.")
            return images, [self._empty_mask_like(image) for image in images]

        return images, masks

    def _fill_missing_batch_pair(self, image, mask):
        if image is None and mask is None:
            raise ValueError("At least one input is required: connect `image`, `mask`, or both.")

        if image is None:
            return self._empty_image_like(mask), mask

        if mask is None:
            return image, self._empty_mask_like(image)

        return image, mask

    def _select_from_list(self, images, masks, index: int, none_when_missing: bool):
        images, masks = self._fill_missing_list_pair(images, masks)
        if len(images) != len(masks):
            raise ValueError(f"Image/mask list length mismatch: {len(images)} images, {len(masks)} masks.")

        count = len(images)
        if count <= 0:
            if none_when_missing:
                empty_image, empty_mask = self.empty_comfy_tensors()
                return (empty_image, empty_mask, False)
            raise ValueError("Image list is empty.")

        selected_index = self._normalize_index(index, count)
        if selected_index is None:
            if none_when_missing:
                empty_image, empty_mask = self.empty_comfy_tensors()
                return (empty_image, empty_mask, False)
            raise ValueError(
                f"Index out of range: index={index}, valid range is [0, {count - 1}] or negative equivalent."
            )

        selected_image = images[selected_index]
        selected_mask = masks[selected_index]
        return self._validate_and_return_selected(selected_image, selected_mask, none_when_missing)

    def _select_from_batch(self, image: torch.Tensor, mask: torch.Tensor, index: int, none_when_missing: bool):
        image, mask = self._fill_missing_batch_pair(image, mask)
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
        return self._validate_and_return_selected(selected_image, selected_mask, none_when_missing)

    @staticmethod
    def _normalize_index(index: int, count: int):
        selected_index = int(index)
        if selected_index < 0:
            selected_index += count
        if selected_index < 0 or selected_index >= count:
            return None
        return selected_index

    def _validate_and_return_selected(
        self,
        selected_image: torch.Tensor,
        selected_mask: torch.Tensor,
        none_when_missing: bool,
    ):
        if selected_image.ndim != 4 or selected_mask.ndim != 3:
            raise ValueError("Invalid selected tensor shape for `image` or `mask`.")

        has_image = not self._is_placeholder(selected_image, selected_mask)

        if not has_image and not none_when_missing:
            raise ValueError("Selected image is empty placeholder while `none_when_missing` is False.")

        return (selected_image, selected_mask, has_image)

    def select(self, index: int = 0, none_when_missing: bool = True, image=None, mask=None):
        if image is None and mask is None:
            raise ValueError("At least one input is required: connect `image`, `mask`, or both.")

        if self._is_list_input(image) or self._is_list_input(mask):
            return self._select_from_list(image, mask, index, none_when_missing)

        return self._select_from_batch(image, mask, index, none_when_missing)
