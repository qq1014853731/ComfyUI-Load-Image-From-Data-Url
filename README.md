# ComfyUI Load Image From Data URL

[中文文档](./README.zh-CN.md)

Open-source ComfyUI custom nodes for loading images from URLs, local paths, and S3, plus simple batch loading and batch selection.

The batch loader uses independent URI fields that can be added with a `+ Add URI` button. It does not split a single string by commas or newlines, so data URLs can contain arbitrary payload text safely.

## Included Nodes

- `Load Image From URI` (`LoadImageFromURI`)
- `Load Image From URI (Batch)` (`LoadImageFromURIBatch`)
- `Load Image From URI (List)` (`LoadImageFromURIList`)
- `Batch Load Image Selector` (`BatchLoadImageSelector`)
- `Load Image Selector (List)` (`LoadImageSelectorList`)

## Install

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/qq1014853731/ComfyUI-Load-Image-From-Data-Url.git
```

Install dependencies in the same Python environment used by ComfyUI:

```bash
pip install -r requirements.txt
```

Restart ComfyUI after installation.

After updating this node, refresh the browser page as well so ComfyUI loads the frontend extension for the batch `+ Add URI` button.

## What You Can Input

- `data:` URL
- `http://` / `https://` / `ftp://`
- `s3://bucket/key`
- `file://`
- local file path
- Windows drive path such as `C:\\example.png`
- relative path such as `./input/example.png`

Relative paths are resolved from the current working directory of the ComfyUI process.

## Node Usage

### Load Image From URI

Use this node when you want to load **one image**.

- `uri`: image address or path
- `timeout`: request timeout in seconds, `0` means no explicit timeout
- `max_download_bytes`: maximum download size in bytes, `0` means no explicit limit
- `allow_empty`: if enabled, empty input returns an empty placeholder instead of stopping the workflow

Best for:
- loading one remote image
- loading one local image
- loading one S3 image

### Load Image From URI (Batch)

Use this node when you want to load **multiple images as one batch tensor**.

- Click `+ Add URI` to add one independent URI/path field per image
- Other parameters are the same as the single-image node
- `size_mode`:
  - `pad_to_max`: output one batch tensor by padding smaller images/masks to the largest width and height
  - `resize_to_first`: output one batch tensor by resizing later images/masks to the first image size
  - `error`: stop when any image size differs

Best for:
- sending multiple images into nodes that support batch input
- forcing a single batch tensor output

### Load Image From URI (List)

Use this node when you want to load **multiple images while preserving each original resolution**.

- Click `+ Add URI` to add one independent URI/path field per image
- Outputs a ComfyUI list of individual `IMAGE` / `MASK` tensors
- Does not resize or pad images

### Batch Load Image Selector

Use this node after `Load Image From URI (Batch)` when you want to pick **one image** from a batch tensor.

- `index`: which image to pick
  - `0` = first image
  - `1` = second image
  - `-1` = last image
- `none_when_missing`:
  - `True`: if index is out of range, return an empty result
  - `False`: if index is out of range, stop with an error
- `image` and `mask` are optional, but at least one must be connected.
  - image only: selector creates a zero mask with the selected image size
  - mask only: selector creates a black image with the selected mask size

Best for:
- selecting one image from a loaded batch tensor
- building optional or index-based workflows

### Load Image Selector (List)

Use this node after `Load Image From URI (List)` when you want to pick **one image** from a ComfyUI image list while keeping the selected image's original resolution.

Inputs match `Batch Load Image Selector`, but this node consumes the full list at once and selects by list index.

## Simple Examples

### Single image

```text
https://example.com/image.png
```

```text
s3://my-bucket/path/to/image.png
```

```text
./input/example.png
```

### Batch image list

Use the `+ Add URI` button and put each value in its own URI field. Each URI field has its own `Remove` button, and remaining fields are renumbered continuously after deletion.

## S3 Notes

S3 uses `boto3` and AWS default credentials. You can also use environment variables such as:

```bash
AWS_ENDPOINT_URL=http://127.0.0.1:9000
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_SESSION_TOKEN=...
```

`AWS_ENDPOINT_URL` is useful for MinIO or other S3-compatible services.

## License

MIT. See [LICENSE](./LICENSE).
