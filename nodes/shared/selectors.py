from .tensors import empty_comfy_tensors, empty_image_like, empty_mask_like, is_placeholder, normalize_index


def select_from_batch(image, mask, index: int, none_when_missing: bool):
    if image is None and mask is None:
        raise ValueError("At least one input is required: connect `image`, `mask`, or both.")

    if image is None:
        image = empty_image_like(mask)
    if mask is None:
        mask = empty_mask_like(image)

    if image.ndim != 4 or mask.ndim != 3:
        raise ValueError("Invalid batch tensor shape for `image` or `mask`.")

    batch_size = int(image.shape[0])
    if batch_size <= 0:
        if none_when_missing:
            empty_image, empty_mask = empty_comfy_tensors()
            return empty_image, empty_mask, False
        raise ValueError("Image batch is empty.")

    selected_index = normalize_index(index, batch_size)
    if selected_index is None:
        if none_when_missing:
            empty_image, empty_mask = empty_comfy_tensors()
            return empty_image, empty_mask, False
        raise ValueError(
            f"Index out of range: index={index}, valid range is [0, {batch_size - 1}] or negative equivalent."
        )

    selected_image = image[selected_index : selected_index + 1]
    selected_mask = mask[selected_index : selected_index + 1]
    return validate_selected(selected_image, selected_mask, none_when_missing)


def select_from_list(images, masks, index: int, none_when_missing: bool):
    if images is None and masks is None:
        raise ValueError("At least one input is required: connect `image`, `mask`, or both.")

    if images is None:
        images = [empty_image_like(mask_tensor) for mask_tensor in masks]
    if masks is None:
        masks = [empty_mask_like(image_tensor) for image_tensor in images]

    if len(images) != len(masks):
        raise ValueError(f"Image/mask list length mismatch: {len(images)} images, {len(masks)} masks.")

    selected_index = normalize_index(index, len(images))
    if selected_index is None:
        if none_when_missing:
            empty_image, empty_mask = empty_comfy_tensors()
            return empty_image, empty_mask, False
        raise ValueError(
            f"Index out of range: index={index}, valid range is [0, {len(images) - 1}] or negative equivalent."
        )

    return validate_selected(images[selected_index], masks[selected_index], none_when_missing)


def validate_selected(selected_image, selected_mask, none_when_missing: bool):
    if selected_image.ndim != 4 or selected_mask.ndim != 3:
        raise ValueError("Invalid selected tensor shape for `image` or `mask`.")

    has_image = not is_placeholder(selected_image, selected_mask)
    if not has_image and not none_when_missing:
        raise ValueError("Selected image is empty placeholder while `none_when_missing` is False.")

    return selected_image, selected_mask, has_image
