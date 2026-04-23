from .nodes import (
    LoadImageFromURI,
    LoadImageFromURIBatch,
    LoadImageFromURIList,
    LoadImageSelectorBatch,
    LoadImageSelectorList,
)

WEB_DIRECTORY = "./web"


NODE_CLASS_MAPPINGS = {
    "LoadImageFromURI": LoadImageFromURI,
    "LoadImageFromURIBatch": LoadImageFromURIBatch,
    "LoadImageFromURIList": LoadImageFromURIList,
    "LoadImageSelectorBatch": LoadImageSelectorBatch,
    "LoadImageSelectorList": LoadImageSelectorList,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromURI": "Load Image From URI",
    "LoadImageFromURIBatch": "Load Image From URI (Batch)",
    "LoadImageFromURIList": "Load Image From URI (List)",
    "LoadImageSelectorBatch": "Load Image Selector (Batch)",
    "LoadImageSelectorList": "Load Image Selector (List)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
