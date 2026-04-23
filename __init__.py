from .nodes import BatchLoadImageSelector, LoadImageFromURI, LoadImageFromURIBatch

WEB_DIRECTORY = "./web"


NODE_CLASS_MAPPINGS = {
    "LoadImageFromURI": LoadImageFromURI,
    "LoadImageFromURIBatch": LoadImageFromURIBatch,
    "BatchLoadImageSelector": BatchLoadImageSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromURI": "Load Image From URI",
    "LoadImageFromURIBatch": "Load Image From URI (Batch)",
    "BatchLoadImageSelector": "Batch Load Image Selector",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
