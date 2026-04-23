import torch


def empty_comfy_tensors():
    image_tensor = torch.zeros((1, 1, 1, 3), dtype=torch.float32)
    mask_tensor = torch.ones((1, 1, 1), dtype=torch.float32)
    return image_tensor, mask_tensor


def empty_mask_like(image_tensor: torch.Tensor) -> torch.Tensor:
    return torch.zeros(
        (int(image_tensor.shape[0]), int(image_tensor.shape[1]), int(image_tensor.shape[2])),
        dtype=image_tensor.dtype,
        device=image_tensor.device,
    )


def empty_image_like(mask_tensor: torch.Tensor) -> torch.Tensor:
    return torch.zeros(
        (int(mask_tensor.shape[0]), int(mask_tensor.shape[1]), int(mask_tensor.shape[2]), 3),
        dtype=mask_tensor.dtype,
        device=mask_tensor.device,
    )


def is_placeholder(image_tensor: torch.Tensor, mask_tensor: torch.Tensor) -> bool:
    return is_placeholder_image(image_tensor) and is_placeholder_mask(mask_tensor)


def is_placeholder_image(image_tensor: torch.Tensor) -> bool:
    return (
        tuple(image_tensor.shape) == (1, 1, 1, 3)
        and bool(torch.all(image_tensor == 0).item())
    )


def is_placeholder_mask(mask_tensor: torch.Tensor) -> bool:
    return tuple(mask_tensor.shape) == (1, 1, 1) and bool(torch.all(mask_tensor == 1).item())


def resize_comfy_tensors(image_tensor: torch.Tensor, mask_tensor: torch.Tensor, height: int, width: int):
    image_nchw = image_tensor.movedim(-1, 1)
    image_nchw = torch.nn.functional.interpolate(
        image_nchw,
        size=(height, width),
        mode="bilinear",
        align_corners=False,
    )
    resized_image = image_nchw.movedim(1, -1)

    mask_nchw = mask_tensor[:, None, :, :]
    mask_nchw = torch.nn.functional.interpolate(mask_nchw, size=(height, width), mode="nearest")
    resized_mask = mask_nchw[:, 0, :, :]
    return resized_image, resized_mask


def pad_comfy_tensors(image_tensor: torch.Tensor, mask_tensor: torch.Tensor, height: int, width: int):
    current_h = int(image_tensor.shape[1])
    current_w = int(image_tensor.shape[2])
    pad_h = height - current_h
    pad_w = width - current_w

    if pad_h < 0 or pad_w < 0:
        raise ValueError(f"Cannot pad tensor from {(current_h, current_w)} to smaller target {(height, width)}.")

    if pad_h == 0 and pad_w == 0:
        return image_tensor, mask_tensor

    padded_image = torch.nn.functional.pad(image_tensor, (0, 0, 0, pad_w, 0, pad_h), value=0)
    # ComfyUI masks use 1.0 for masked/transparent areas, so padded pixels
    # should be marked as absent image content.
    padded_mask = torch.nn.functional.pad(mask_tensor, (0, pad_w, 0, pad_h), value=1)
    return padded_image, padded_mask


def normalize_index(index: int, count: int):
    selected_index = int(index)
    if selected_index < 0:
        selected_index += count
    if selected_index < 0 or selected_index >= count:
        return None
    return selected_index
