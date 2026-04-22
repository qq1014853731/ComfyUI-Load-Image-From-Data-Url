# ComfyUI Load Image From Data URL

[中文文档](./README.zh-CN.md)

Open-source ComfyUI custom nodes for loading images from URLs, local paths, and S3, plus simple batch loading and batch selection.

## Included Nodes

- `Load Image From URI` (`LoadImageFromURI`)
- `Load Image From URI (Batch)` (`LoadImageFromURIBatch`)
- `Batch Load Image Selector` (`BatchLoadImageSelector`)

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

Use this node when you want to load **multiple images at once**.

- Put **one URI/path per line** into `uris`
- Other parameters are the same as the single-image node
- All images in the same batch should use the same size

Best for:
- loading a list of images from URLs
- loading a list of local files
- sending multiple images into nodes that support batch input

### Batch Load Image Selector

Use this node after the batch loader when you want to pick **one image** from the batch.

- `index`: which image to pick
  - `0` = first image
  - `1` = second image
  - `-1` = last image
- `none_when_missing`:
  - `True`: if index is out of range, return an empty result
  - `False`: if index is out of range, stop with an error

Best for:
- selecting one image from a loaded batch
- building optional or index-based workflows

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

```text
https://example.com/a.png
https://example.com/b.png
https://example.com/c.png
```

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
