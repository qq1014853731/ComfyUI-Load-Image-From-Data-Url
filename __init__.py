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


class LoadImageFromURI:
    """
    Load an image from a URI, URL, or local path.

    Supported inputs:
    - data: URL
      Examples:
        data:image/png;base64,xxxx
    - s3://
      Example:
        s3://my-bucket/path/to/image.png
    - http://
    - https://
    - ftp://
    - file://
    - local file path
      Examples:
        /root/a.png
        C:\\images\\a.png
        ./input/a.png

    Outputs:
    - IMAGE: [1, H, W, C], float32, range 0~1
    - MASK:  [1, H, W], float32
            If the image has an alpha channel, mask = 1 - alpha.
            If there is no alpha channel, a full-zero mask is returned.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "uri": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": ""
                    }
                ),
                "timeout": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 600,
                        "step": 1
                    }
                ),
                "max_download_bytes": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 2147483647,
                        "step": 1048576
                    }
                ),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "load_image_from_uri"
    CATEGORY = "image"
    READ_CHUNK_SIZE = 1024 * 1024

    @staticmethod
    def _normalize_timeout(timeout: int | float | None) -> float | None:
        """
        Normalize timeout value.
        Return None when timeout is not positive.
        """
        if timeout is None:
            return None
        try:
            timeout_value = float(timeout)
        except (TypeError, ValueError):
            return None
        return timeout_value if timeout_value > 0 else None

    @staticmethod
    def _normalize_max_download_bytes(max_download_bytes: int | float | None) -> int | None:
        """
        Normalize max download size.
        Return None when the value is not positive.
        """
        try:
            max_bytes = int(max_download_bytes)
        except (TypeError, ValueError):
            return None

        return max_bytes if max_bytes > 0 else None

    @staticmethod
    def _format_bytes(byte_count: int) -> str:
        if byte_count < 1024 * 1024:
            return f"{byte_count} bytes"
        return f"{byte_count / (1024 * 1024):.1f} MiB"

    def _read_limited_stream(
        self,
        stream,
        source_label: str,
        max_download_bytes: int,
        content_length: int | None = None,
    ) -> bytes:
        """
        Read a remote stream while enforcing a configurable byte limit.
        """
        max_bytes = self._normalize_max_download_bytes(max_download_bytes)

        if max_bytes is not None and content_length is not None and content_length > max_bytes:
            raise ValueError(
                f"{source_label} is too large: {self._format_bytes(content_length)} "
                f"exceeds limit {self._format_bytes(max_bytes)}"
            )

        chunks = []
        total = 0
        while True:
            chunk = stream.read(self.READ_CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if max_bytes is not None and total > max_bytes:
                raise ValueError(
                    f"{source_label} is too large: exceeds limit {self._format_bytes(max_bytes)}"
                )
            chunks.append(chunk)

        return b"".join(chunks)

    def load_image_from_uri(self, uri: str, timeout: int = 0, max_download_bytes: int = 0):
        """
        Main entry point:
        1. Read bytes from the URI.
        2. Open the image with PIL.
        3. Convert it to ComfyUI IMAGE / MASK tensors.
        """
        if not uri or not isinstance(uri, str):
            raise ValueError("`uri` must be a non-empty string.")

        uri = uri.strip()
        if not uri:
            raise ValueError("`uri` must be a non-empty string.")

        image_bytes = self._read_uri(
            uri,
            timeout=timeout,
            max_download_bytes=max_download_bytes,
        )
        pil_image = self._bytes_to_pil_image(image_bytes)
        image_tensor, mask_tensor = self._pil_to_comfy_tensors(pil_image)
        return (image_tensor, mask_tensor)

    def _read_uri(self, uri: str, timeout: int, max_download_bytes: int) -> bytes:
        """
        Read bytes based on URI type.
        """
        # 1. data URL
        if uri.startswith("data:"):
            return self._read_data_url(uri)

        # 2. Windows drive path, e.g. C:\a\b.png
        #    urlparse may misclassify this, so handle it first.
        if re.match(r"^[a-zA-Z]:[\\/]", uri):
            return self._read_local_file(uri)

        parsed = urllib.parse.urlparse(uri)
        scheme = (parsed.scheme or "").lower()

        # 3. file://
        if scheme == "file":
            return self._read_file_url(parsed)

        # 4. s3://
        if scheme == "s3":
            return self._read_s3_url(
                parsed,
                timeout=timeout,
                max_download_bytes=max_download_bytes,
            )

        # 5. http / https / ftp
        if scheme in ("http", "https", "ftp"):
            return self._read_remote_url(
                uri,
                timeout=timeout,
                max_download_bytes=max_download_bytes,
            )

        # 6. No scheme: treat as a local path.
        if scheme == "":
            return self._read_local_file(uri)

        raise ValueError(f"Unsupported URI scheme: {scheme}")

    def _read_data_url(self, uri: str) -> bytes:
        """
        Parse a data URL.

        Supported formats:
        - data:image/png;base64,xxxx
        - data:;base64,xxxx
        """
        # data:[<mediatype>][;base64],<data>
        if "," not in uri:
            raise ValueError("Invalid data URL: missing comma separator.")

        header, data_part = uri.split(",", 1)

        # Header examples:
        # data:image/png;base64
        # data:text/plain;charset=utf-8
        # data:;base64
        is_base64 = ";base64" in header.lower()

        try:
            if is_base64:
                # Base64 payload may contain line breaks, strip whitespace first.
                cleaned = re.sub(r"\s+", "", data_part)
                return base64.b64decode(cleaned, validate=True)
            else:
                # Non-base64 data URL: decode as URL-encoded bytes.
                decoded = urllib.parse.unquote_to_bytes(data_part)
                return decoded
        except Exception as e:
            raise ValueError(f"Failed to parse data URL: {e}")

    def _read_local_file(self, path_str: str) -> bytes:
        """
        Read a local file path.
        Supports absolute and relative paths.
        """
        path = Path(path_str).expanduser()

        if not path.exists():
            raise FileNotFoundError(f"Local file does not exist: {path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        return path.read_bytes()

    def _read_file_url(self, parsed: urllib.parse.ParseResult) -> bytes:
        """
        Read a file:// URL.
        Compatible with Linux and Windows.
        """
        # file:///tmp/a.png
        # file:///C:/Users/xx/a.png
        # file://localhost/tmp/a.png

        netloc = parsed.netloc
        path = urllib.request.url2pathname(parsed.path)

        # For file://localhost/path, ignore localhost.
        if netloc and netloc.lower() not in ("localhost",):
            # On some systems, file://server/share is a network path.
            # Rebuild it for basic compatibility.
            path = f"//{netloc}{path}"

        return self._read_local_file(path)

    def _read_s3_url(
        self,
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
        """
        Read s3://bucket/key.
        """
        bucket = parsed.netloc
        key = urllib.parse.unquote(parsed.path.lstrip("/"))

        if not bucket:
            raise ValueError("Invalid s3 URI: missing bucket, e.g. s3://my-bucket/a.png")

        if not key:
            raise ValueError("Invalid s3 URI: missing object key, e.g. s3://my-bucket/path/a.png")

        # Allow node parameters to override environment variables.
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

        normalized_timeout = self._normalize_timeout(timeout)
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
                return self._read_limited_stream(
                    body,
                    source_label=f"S3 object s3://{bucket}/{key}",
                    max_download_bytes=max_download_bytes,
                    content_length=content_length,
                )
        except Exception as e:
            raise ValueError(f"Failed to read S3 object s3://{bucket}/{key}: {e}")

    def _read_remote_url(self, url: str, timeout: int, max_download_bytes: int) -> bytes:
        """
        Read remote content from http / https / ftp.
        Uses the standard library urllib.
        """
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "ComfyUI-LoadImageFromURI/1.0"},
        )

        try:
            normalized_timeout = self._normalize_timeout(timeout)
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
                return self._read_limited_stream(
                    response,
                    source_label=f"Remote URL {url}",
                    max_download_bytes=max_download_bytes,
                    content_length=content_length,
                )
        except urllib.error.HTTPError as e:
            raise ValueError(f"Remote request failed with HTTP status {e.code}: {url}")
        except urllib.error.URLError as e:
            raise ValueError(f"Failed to fetch remote URL: {url}, reason: {e.reason}")

    def _bytes_to_pil_image(self, image_bytes: bytes) -> Image.Image:
        """
        Convert bytes to a PIL.Image.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image = ImageOps.exif_transpose(image)
            image.load()  # Force full read to avoid deferred I/O errors.
            return image
        except Exception as e:
            raise ValueError(f"Failed to decode image: {e}")

    def _pil_to_comfy_tensors(self, image: Image.Image):
        """
        Convert a PIL image to ComfyUI IMAGE / MASK tensors.
        """
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


NODE_CLASS_MAPPINGS = {
    "LoadImageFromURI": LoadImageFromURI,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromURI": "Load Image From URI",
}
