import torch

from .utils import ImageNodeUtils


class LoadImageFromURIBatch(ImageNodeUtils):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "uris": ("STRING", {"multiline": True, "default": ""}),
                "timeout": ("INT", {"default": 0, "min": 0, "max": 600, "step": 1}),
                "max_download_bytes": (
                    "INT",
                    {"default": 0, "min": 0, "max": 2147483647, "step": 1048576},
                ),
                "allow_empty": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "BOOLEAN", "INT")
    RETURN_NAMES = ("image", "mask", "has_image", "count")
    FUNCTION = "load_images_from_uri_batch"
    CATEGORY = "image"

    def load_images_from_uri_batch(
        self,
        uris: str,
        timeout: int = 0,
        max_download_bytes: int = 0,
        allow_empty: bool = False,
    ):
        if not isinstance(uris, str):
            if allow_empty:
                image_tensor, mask_tensor = self.empty_comfy_tensors()
                return (image_tensor, mask_tensor, False, 0)
            raise ValueError("`uris` must be a string with one URI per line.")

        uri_list = [line.strip() for line in uris.splitlines() if line.strip()]
        if not uri_list:
            if allow_empty:
                image_tensor, mask_tensor = self.empty_comfy_tensors()
                return (image_tensor, mask_tensor, False, 0)
            raise ValueError("`uris` is empty. Provide at least one non-empty URI line.")

        image_tensors = []
        mask_tensors = []
        expected_hw = None

        for idx, uri in enumerate(uri_list):
            image_bytes = self.read_uri(uri, timeout=timeout, max_download_bytes=max_download_bytes)
            pil_image = self.bytes_to_pil_image(image_bytes)
            image_tensor, mask_tensor = self.pil_to_comfy_tensors(pil_image)

            current_hw = image_tensor.shape[1:3]
            if expected_hw is None:
                expected_hw = current_hw
            elif current_hw != expected_hw:
                raise ValueError(
                    f"Image size mismatch at line {idx + 1}: expected {expected_hw}, got {current_hw}."
                )

            image_tensors.append(image_tensor)
            mask_tensors.append(mask_tensor)

        batch_image = torch.cat(image_tensors, dim=0)
        batch_mask = torch.cat(mask_tensors, dim=0)
        return (batch_image, batch_mask, True, len(uri_list))
