# ComfyUI Load Image From Data URL

[中文文档 (Chinese README)](./README.zh-CN.md)

A lightweight open-source ComfyUI custom node that loads images from multiple URI sources and outputs standard ComfyUI `IMAGE` and `MASK` tensors.

## Features

- Supports `data:` URLs (base64 and URL-encoded payloads)
- Supports `s3://` URIs via `boto3`
- Supports remote URLs: `http://`, `https://`, `ftp://`
- Supports `file://` URLs
- Supports local file paths (absolute and relative, including Windows drive paths)
- Outputs:
  - `IMAGE`: shape `[1, H, W, C]`, `float32`, value range `0~1`
  - `MASK`: shape `[1, H, W]`, `float32`
    - If input has alpha channel: `mask = 1 - alpha`
    - If no alpha channel: returns a zero mask
    - If `uri` is empty: returns a 1x1 blank image with a full mask
  - `HAS_IMAGE`: `BOOLEAN`
    - `True` when an image was loaded
    - `False` when `uri` was empty and the placeholder output was returned
- Uses Python standard library `urllib` for remote fetch (no `requests` dependency)
- Can limit remote and S3 download size to avoid unbounded memory use

## Repository Structure

- `__init__.py`: Node implementation and ComfyUI node registration
- `requirements.txt`: Python dependencies

## Requirements

- Python environment used by ComfyUI
- ComfyUI installed and running
- Python packages:
  - `numpy`
  - `torch`
  - `Pillow`
  - `boto3` (currently listed in this repository)

Install dependencies in your ComfyUI Python environment:

```bash
pip install -r requirements.txt
```

## Installation

Clone or copy this repository into your ComfyUI custom nodes directory:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/qq1014853731/ComfyUI-Load-Image-From-Data-Url.git
```

Then restart ComfyUI.

## Node Info

- **Node class name**: `LoadImageFromURI`
- **Display name**: `Load Image From URI`
- **Category**: `image`
- **Inputs**:
  - `uri` (`STRING`, multiline): source URI / URL / local path
  - `timeout` (`INT`, default `0`, range `0~600`): remote request timeout in seconds. Set `0` to disable the explicit timeout.
  - `max_download_bytes` (`INT`, default `0`): maximum HTTP/FTP/S3 download size in bytes. Set `0` to disable the size limit.
  - `allow_empty` (`BOOLEAN`, default `False`): when `True`, empty `uri` returns a placeholder output instead of raising an error.
- **Outputs**:
  - `image` (`IMAGE`)
  - `mask` (`MASK`)
  - `has_image` (`BOOLEAN`)

## Usage Examples

### 1) Data URL (base64 PNG)

```text
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
```

### 2) Remote URL

```text
https://example.com/image.png
```

### 3) S3 URI

```text
s3://my-bucket/path/to/image.png
```

S3 access uses `boto3` with the default credential chain, and supports environment overrides.

Credential / endpoint resolution order:

1. Explicit node parameters
2. Environment variables
3. AWS default credential/provider chain

Useful environment variables:

```bash
AWS_ENDPOINT_URL=http://127.0.0.1:9000
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_SESSION_TOKEN=...
```

Notes:

- `timeout` input applies to S3 connect/read timeout.
- `max_download_bytes` input applies to HTTP/FTP/S3 response bodies.
- `AWS_ENDPOINT_URL` lets you use MinIO or other S3-compatible services.
- If no explicit credentials are provided, boto3 falls back to profile/instance role/default chain.
- S3 object keys are URL-decoded, so `s3://bucket/a%20b.png` reads key `a b.png`.

### 4) Local file path

```text
# Absolute path
/Users/yourname/Pictures/sample.png

# Windows specified drive letter
C:\\example.png

# Relative path (ComfyUI folder)
./input/example.png
input/example.png
```

Relative paths are resolved from the current working directory of the ComfyUI process.

Windows:

```text
C:\Users\yourname\Pictures\sample.png
```

### 5) File URL

```text
file:///Users/yourname/Pictures/sample.png
```

## Empty URI and Switch Nodes

When `allow_empty=True` and `uri` is empty (or not a string), the node returns a valid 1x1 placeholder image, a full mask, and `has_image = False`.

When `allow_empty=False` (default), empty `uri` raises `ValueError`.

## Error Handling

The node raises clear Python errors for other common invalid inputs:

- Unsupported URI scheme
- Invalid `data:` URL format
- Missing local file or non-file path
- S3 object read failures (invalid path, permissions, missing object, etc.)
- Remote HTTP/URL fetch failures
- Image decode failures

## Contributing

Issues and pull requests are welcome.

Please include:

- A clear problem description
- Steps to reproduce (if bug-related)
- Expected vs actual behavior
- Environment details (OS, Python, ComfyUI version)

## License

This project is licensed under the [MIT License](./LICENSE).
