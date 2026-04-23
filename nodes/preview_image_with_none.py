from nodes import PreviewImage


class PreviewImageWithNone(PreviewImage):
    SEARCH_ALIASES = [
        "preview with none",
        "preview image with none",
        "show image with none",
        "view image with none",
        "display image with none",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    def save_images(self, images=None, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        # 关键：None 时直接返回空预览，不报错
        if images is None:
            return {"ui": {"images": []}}

        # 其余情况完全走官方 PreviewImage 的逻辑
        # 官方 PreviewImage 本身会写入 temp 目录，而不是 output 目录
        return super().save_images(
            images=images,
            filename_prefix=filename_prefix,
            prompt=prompt,
            extra_pnginfo=extra_pnginfo,
        )
