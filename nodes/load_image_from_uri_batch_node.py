import re

import torch

from .utils import ContainsAnyDict, ImageNodeUtils


class LoadImageFromURIBatch(ImageNodeUtils):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "timeout": ("INT", {"default": 0, "min": 0, "max": 600, "step": 1}),
                "max_download_bytes": (
                    "INT",
                    {"default": 0, "min": 0, "max": 2147483647, "step": 1048576},
                ),
                "output_mode": (
                    ["list_original", "batch_pad_to_max", "batch_resize_to_first", "batch_error"],
                    {"default": "list_original"},
                ),
                "allow_empty": ("BOOLEAN", {"default": False}),
            },
            # uri_1, uri_2, ... are created by the frontend extension at runtime.
            "optional": ContainsAnyDict(),
        }

    RETURN_TYPES = ("IMAGE", "MASK", "BOOLEAN", "INT")
    RETURN_NAMES = ("image", "mask", "has_image", "count")
    OUTPUT_IS_LIST = (True, True, False, False)
    FUNCTION = "load_images_from_uri_batch"
    CATEGORY = "image"

    @staticmethod
    def _uri_sort_key(key: str):
        # Numeric sorting keeps uri_10 after uri_2. Plain string sorting would not.
        match = re.match(r"^uri_(\d+)$", key)
        return (0, int(match.group(1))) if match else (1, key)

    def load_images_from_uri_batch(
        self,
        timeout: int = 0,
        max_download_bytes: int = 0,
        output_mode: str = "list_original",
        allow_empty: bool = False,
        **kwargs,
    ):
        uri_list = []
        # Dynamic URI widgets arrive through kwargs because they are not declared
        # individually in INPUT_TYPES.
        for key in sorted(kwargs, key=self._uri_sort_key):
            if not key.startswith("uri_"):
                continue
            uri = kwargs[key]
            if not isinstance(uri, str):
                continue
            uri = uri.strip()
            if uri:
                uri_list.append(uri)

        if not uri_list:
            if allow_empty:
                image_tensor, mask_tensor = self.empty_comfy_tensors()
                return ([image_tensor], [mask_tensor], False, 0)
            raise ValueError("URI batch is empty. Add at least one non-empty URI item.")

        image_tensors = []
        mask_tensors = []
        for idx, uri in enumerate(uri_list):
            image_bytes = self.read_uri(uri, timeout=timeout, max_download_bytes=max_download_bytes)
            pil_image = self.bytes_to_pil_image(image_bytes)
            image_tensor, mask_tensor = self.pil_to_comfy_tensors(pil_image)
            image_tensors.append(image_tensor)
            mask_tensors.append(mask_tensor)

        if output_mode == "list_original":
            return (image_tensors, mask_tensors, True, len(uri_list))

        size_mode = output_mode.removeprefix("batch_")
        image_tensors, mask_tensors = self.normalize_batch_tensor_sizes(
            image_tensors,
            mask_tensors,
            size_mode=size_mode,
        )
        batch_image = torch.cat(image_tensors, dim=0)
        batch_mask = torch.cat(mask_tensors, dim=0)
        return ([batch_image], [batch_mask], True, len(uri_list))

    def normalize_batch_tensor_sizes(self, image_tensors, mask_tensors, size_mode: str):
        sizes = [tuple(image_tensor.shape[1:3]) for image_tensor in image_tensors]
        if len(set(sizes)) == 1:
            return image_tensors, mask_tensors

        if size_mode == "error":
            expected_hw = sizes[0]
            for idx, current_hw in enumerate(sizes[1:], start=2):
                if current_hw != expected_hw:
                    raise ValueError(
                        f"Image size mismatch at item {idx}: expected {expected_hw}, got {current_hw}. "
                        "Use `pad_to_max` to preserve image content without scaling, or `resize_to_first` to resize."
                    )

        if size_mode == "resize_to_first":
            target_h, target_w = sizes[0]
            return self.resize_batch_tensors(image_tensors, mask_tensors, int(target_h), int(target_w))

        if size_mode == "pad_to_max":
            target_h = max(int(size[0]) for size in sizes)
            target_w = max(int(size[1]) for size in sizes)
            return self.pad_batch_tensors(image_tensors, mask_tensors, target_h, target_w)

        raise ValueError(f"Unsupported size_mode: {size_mode}")

    def resize_batch_tensors(self, image_tensors, mask_tensors, target_h: int, target_w: int):
        resized_images = []
        resized_masks = []
        for image_tensor, mask_tensor in zip(image_tensors, mask_tensors):
            image_tensor, mask_tensor = self.resize_comfy_tensors(
                image_tensor,
                mask_tensor,
                height=target_h,
                width=target_w,
            )
            resized_images.append(image_tensor)
            resized_masks.append(mask_tensor)
        return resized_images, resized_masks

    def pad_batch_tensors(self, image_tensors, mask_tensors, target_h: int, target_w: int):
        padded_images = []
        padded_masks = []
        for image_tensor, mask_tensor in zip(image_tensors, mask_tensors):
            image_tensor, mask_tensor = self.pad_comfy_tensors(
                image_tensor,
                mask_tensor,
                height=target_h,
                width=target_w,
            )
            padded_images.append(image_tensor)
            padded_masks.append(mask_tensor)
        return padded_images, padded_masks
