import torch

from .tensors import pad_comfy_tensors, resize_comfy_tensors


def normalize_batch_tensor_sizes(image_tensors, mask_tensors, size_mode: str):
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
        return resize_batch_tensors(image_tensors, mask_tensors, int(target_h), int(target_w))

    if size_mode == "pad_to_max":
        target_h = max(int(size[0]) for size in sizes)
        target_w = max(int(size[1]) for size in sizes)
        return pad_batch_tensors(image_tensors, mask_tensors, target_h, target_w)

    raise ValueError(f"Unsupported size_mode: {size_mode}")


def resize_batch_tensors(image_tensors, mask_tensors, target_h: int, target_w: int):
    resized_images = []
    resized_masks = []
    for image_tensor, mask_tensor in zip(image_tensors, mask_tensors):
        image_tensor, mask_tensor = resize_comfy_tensors(
            image_tensor,
            mask_tensor,
            height=target_h,
            width=target_w,
        )
        resized_images.append(image_tensor)
        resized_masks.append(mask_tensor)
    return resized_images, resized_masks


def pad_batch_tensors(image_tensors, mask_tensors, target_h: int, target_w: int):
    padded_images = []
    padded_masks = []
    for image_tensor, mask_tensor in zip(image_tensors, mask_tensors):
        image_tensor, mask_tensor = pad_comfy_tensors(
            image_tensor,
            mask_tensor,
            height=target_h,
            width=target_w,
        )
        padded_images.append(image_tensor)
        padded_masks.append(mask_tensor)
    return padded_images, padded_masks


def cat_image_mask_batch(image_tensors, mask_tensors):
    return torch.cat(image_tensors, dim=0), torch.cat(mask_tensors, dim=0)
