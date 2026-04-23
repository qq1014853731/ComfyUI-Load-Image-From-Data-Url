from .missing import MISSING_POLICIES, validate_missing_policy
from .tensors import (
    empty_comfy_tensors,
    empty_image_like,
    empty_mask_like,
    is_placeholder_image,
    is_placeholder_mask,
    normalize_index,
)


def select_from_batch(image, mask, index: int, image_missing: str, mask_missing: str):
    validate_missing_policy(image_missing, "image_missing")
    validate_missing_policy(mask_missing, "mask_missing")

    if image is not None and image.ndim != 4:
        raise ValueError("Invalid batch tensor shape for `image`.")
    if mask is not None and mask.ndim != 3:
        raise ValueError("Invalid batch tensor shape for `mask`.")

    selected_image = select_optional_batch_tensor(image, index)
    selected_mask = select_optional_batch_tensor(mask, index)
    return resolve_selected(selected_image, selected_mask, image_missing, mask_missing)


def select_from_list(images, masks, index: int, image_missing: str, mask_missing: str):
    validate_missing_policy(image_missing, "image_missing")
    validate_missing_policy(mask_missing, "mask_missing")

    selected_image = select_optional_list_tensor(images, index)
    selected_mask = select_optional_list_tensor(masks, index)
    return resolve_selected(selected_image, selected_mask, image_missing, mask_missing)


def select_optional_batch_tensor(tensor, index: int):
    if tensor is None:
        return None
    selected_index = normalize_index(index, int(tensor.shape[0]))
    if selected_index is None:
        return None
    return tensor[selected_index : selected_index + 1]


def select_optional_list_tensor(tensors, index: int):
    if tensors is None:
        return None
    selected_index = normalize_index(index, len(tensors))
    if selected_index is None:
        return None
    return tensors[selected_index]


def resolve_selected(selected_image, selected_mask, image_missing: str, mask_missing: str):
    if selected_image is not None and selected_image.ndim != 4:
        raise ValueError("Invalid selected tensor shape for `image`.")
    if selected_mask is not None and selected_mask.ndim != 3:
        raise ValueError("Invalid selected tensor shape for `mask`.")

    image_is_placeholder = selected_image is not None and is_placeholder_image(selected_image)
    mask_is_placeholder = selected_mask is not None and is_placeholder_mask(selected_mask)
    has_image = selected_image is not None and not image_is_placeholder

    if image_is_placeholder:
        selected_image = None
    if mask_is_placeholder:
        selected_mask = None

    selected_image = resolve_missing_image(selected_image, selected_mask, image_missing)
    selected_mask = resolve_missing_mask(selected_mask, selected_image, mask_missing)

    return selected_image, selected_mask, has_image


def resolve_missing_image(selected_image, selected_mask, policy: str):
    if selected_image is not None:
        return selected_image
    if policy == "None":
        return None
    if policy == "Throw error":
        raise ValueError("Selected image is missing.")
    if selected_mask is not None:
        return empty_image_like(selected_mask)
    empty_image, _ = empty_comfy_tensors()
    return empty_image


def resolve_missing_mask(selected_mask, selected_image, policy: str):
    if selected_mask is not None:
        return selected_mask
    if policy == "None":
        return None
    if policy == "Throw error":
        raise ValueError("Selected mask is missing.")
    if selected_image is not None:
        return empty_mask_like(selected_image)
    _, empty_mask = empty_comfy_tensors()
    return empty_mask
