import base64
import contextlib
import io
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import boto3
import numpy as np
import torch
from botocore.config import Config
from PIL import Image, ImageOps


READ_CHUNK_SIZE = 1024 * 1024


def normalize_timeout(timeout: int | float | None) -> float | None:
    if timeout is None:
        return None
    try:
        timeout_value = float(timeout)
    except (TypeError, ValueError):
        return None
    return timeout_value if timeout_value > 0 else None


def normalize_max_download_bytes(max_download_bytes: int | float | None) -> int | None:
    try:
        max_bytes = int(max_download_bytes)
    except (TypeError, ValueError):
        return None
    return max_bytes if max_bytes > 0 else None


def format_bytes(byte_count: int) -> str:
    if byte_count < 1024 * 1024:
        return f"{byte_count} bytes"
    return f"{byte_count / (1024 * 1024):.1f} MiB"


def read_limited_stream(stream, source_label: str, max_download_bytes: int, content_length: int | None = None) -> bytes:
    max_bytes = normalize_max_download_bytes(max_download_bytes)
    if max_bytes is not None and content_length is not None and content_length > max_bytes:
        raise ValueError(
            f"{source_label} is too large: {format_bytes(content_length)} "
            f"exceeds limit {format_bytes(max_bytes)}"
        )

    chunks = []
    total = 0
    while True:
        chunk = stream.read(READ_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if max_bytes is not None and total > max_bytes:
            raise ValueError(f"{source_label} is too large: exceeds limit {format_bytes(max_bytes)}")
        chunks.append(chunk)
    return b"".join(chunks)


def read_uri(uri: str, timeout: int, max_download_bytes: int) -> bytes:
    if uri.startswith("data:"):
        return read_data_url(uri)

    if re.match(r"^[a-zA-Z]:[\\/]", uri):
        return read_local_file(uri)

    parsed = urllib.parse.urlparse(uri)
    scheme = (parsed.scheme or "").lower()

    if scheme == "file":
        return read_file_url(parsed)
    if scheme == "s3":
        return read_s3_url(parsed, timeout=timeout, max_download_bytes=max_download_bytes)
    if scheme in ("http", "https", "ftp"):
        return read_remote_url(uri, timeout=timeout, max_download_bytes=max_download_bytes)
    if scheme == "":
        return read_local_file(uri)
    raise ValueError(f"Unsupported URI scheme: {scheme}")


def read_data_url(uri: str) -> bytes:
    if "," not in uri:
        raise ValueError("Invalid data URL: missing comma separator.")
    header, data_part = uri.split(",", 1)
    is_base64 = ";base64" in header.lower()
    try:
        if is_base64:
            cleaned = re.sub(r"\s+", "", data_part)
            return base64.b64decode(cleaned, validate=True)
        return urllib.parse.unquote_to_bytes(data_part)
    except Exception as e:
        raise ValueError(f"Failed to parse data URL: {e}")


def read_local_file(path_str: str) -> bytes:
    path = Path(path_str).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Local file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    return path.read_bytes()


def read_file_url(parsed: urllib.parse.ParseResult) -> bytes:
    netloc = parsed.netloc
    path = urllib.request.url2pathname(parsed.path)
    if netloc and netloc.lower() not in ("localhost",):
        path = f"//{netloc}{path}"
    return read_local_file(path)


def read_s3_url(
    parsed: urllib.parse.ParseResult,
    timeout: int,
    max_download_bytes: int,
    endpoint_url: str = "",
    region: str = "",
    access_key_id: str = "",
    secret_access_key: str = "",
    session_token: str = "",
    force_path_style: bool = False,
) -> bytes:
    bucket = parsed.netloc
    key = urllib.parse.unquote(parsed.path.lstrip("/"))
    if not bucket:
        raise ValueError("Invalid s3 URI: missing bucket, e.g. s3://my-bucket/a.png")
    if not key:
        raise ValueError("Invalid s3 URI: missing object key, e.g. s3://my-bucket/path/a.png")

    endpoint_url = endpoint_url or os.getenv("AWS_ENDPOINT_URL", "")
    region = region or os.getenv("AWS_DEFAULT_REGION", "") or os.getenv("AWS_REGION", "")
    access_key_id = access_key_id or os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_access_key = secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY", "")
    session_token = session_token or os.getenv("AWS_SESSION_TOKEN", "")

    client_kwargs = {}
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url
    if region:
        client_kwargs["region_name"] = region
    if access_key_id:
        client_kwargs["aws_access_key_id"] = access_key_id
    if secret_access_key:
        client_kwargs["aws_secret_access_key"] = secret_access_key
    if session_token:
        client_kwargs["aws_session_token"] = session_token

    normalized_timeout = normalize_timeout(timeout)
    config_kwargs = {}
    if normalized_timeout is not None:
        config_kwargs["connect_timeout"] = normalized_timeout
        config_kwargs["read_timeout"] = normalized_timeout
    if force_path_style:
        config_kwargs["s3"] = {"addressing_style": "path"}
    client_kwargs["config"] = Config(**config_kwargs)

    try:
        client = boto3.client("s3", **client_kwargs)
        response = client.get_object(Bucket=bucket, Key=key)
        content_length = response.get("ContentLength")
        with contextlib.closing(response["Body"]) as body:
            return read_limited_stream(
                body,
                source_label=f"S3 object s3://{bucket}/{key}",
                max_download_bytes=max_download_bytes,
                content_length=content_length,
            )
    except Exception as e:
        raise ValueError(f"Failed to read S3 object s3://{bucket}/{key}: {e}")


def read_remote_url(url: str, timeout: int, max_download_bytes: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "ComfyUI-LoadImageFromURI/1.0"})
    try:
        normalized_timeout = normalize_timeout(timeout)
        if normalized_timeout is None:
            response_context = urllib.request.urlopen(request)
        else:
            response_context = urllib.request.urlopen(request, timeout=normalized_timeout)
        with response_context as response:
            content_length_header = response.headers.get("Content-Length")
            try:
                content_length = int(content_length_header) if content_length_header else None
            except ValueError:
                content_length = None
            return read_limited_stream(
                response,
                source_label=f"Remote URL {url}",
                max_download_bytes=max_download_bytes,
                content_length=content_length,
            )
    except urllib.error.HTTPError as e:
        raise ValueError(f"Remote request failed with HTTP status {e.code}: {url}")
    except urllib.error.URLError as e:
        raise ValueError(f"Failed to fetch remote URL: {url}, reason: {e.reason}")


def bytes_to_pil_image(image_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)
        image.load()
        return image
    except Exception as e:
        raise ValueError(f"Failed to decode image: {e}")


def pil_to_comfy_tensors(image: Image.Image):
    has_alpha = "A" in image.getbands()
    if has_alpha:
        rgba_image = image.convert("RGBA")
        alpha = np.array(rgba_image.getchannel("A"), dtype=np.float32) / 255.0
        rgb_image = rgba_image.convert("RGB")
    else:
        rgb_image = image.convert("RGB")
        alpha = None

    image_np = np.array(rgb_image, dtype=np.float32) / 255.0
    image_tensor = torch.from_numpy(image_np)[None, ...]
    if alpha is not None:
        mask_np = 1.0 - alpha
    else:
        h, w = image_np.shape[:2]
        mask_np = np.zeros((h, w), dtype=np.float32)
    mask_tensor = torch.from_numpy(mask_np)[None, ...]
    return image_tensor, mask_tensor


def load_uri_to_tensors(uri: str, timeout: int, max_download_bytes: int):
    image_bytes = read_uri(uri, timeout=timeout, max_download_bytes=max_download_bytes)
    pil_image = bytes_to_pil_image(image_bytes)
    return pil_to_comfy_tensors(pil_image)
