# ComfyUI Load Image From Data URL

[English README](./README.md)

这是一个用于 ComfyUI 的开源自定义节点集合，支持从 URL、本地路径、S3 加载图片，也支持批量加载和批量选择。

## 包含的节点

- `Load Image From URI`（`LoadImageFromURI`）
- `Load Image From URI (Batch)`（`LoadImageFromURIBatch`）
- `Batch Load Image Selector`（`BatchLoadImageSelector`）

## 安装

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/qq1014853731/ComfyUI-Load-Image-From-Data-Url.git
```

在 ComfyUI 对应 Python 环境安装依赖：

```bash
pip install -r requirements.txt
```

安装后重启 ComfyUI。

## 支持的输入

- `data:` URL
- `http://` / `https://` / `ftp://`
- `s3://bucket/key`
- `file://`
- 本地文件路径
- Windows 盘符路径，例如 `C:\\example.png`
- 相对路径，例如 `./input/example.png`

相对路径会基于 ComfyUI 进程当前工作目录解析。

## 节点用法

### Load Image From URI

这个节点用于加载**单张图片**。

- `uri`：图片地址或路径
- `timeout`：请求超时时间，单位秒，`0` 表示不显式设置超时
- `max_download_bytes`：下载大小限制，单位字节，`0` 表示不显式限制
- `allow_empty`：开启后，空输入不会报错，而是返回空占位结果

适合：
- 加载单张网络图片
- 加载单张本地图片
- 加载单张 S3 图片

### Load Image From URI (Batch)

这个节点用于一次加载**多张图片**。

- 在 `uris` 中每行填写一个 URI/路径
- 其他参数含义与单图节点相同
- 同一批次内的图片建议保持相同尺寸

适合：
- 批量加载多张网络图片
- 批量加载多张本地图片
- 把多张图片送入支持 batch 输入的节点

### Batch Load Image Selector

这个节点用于从批量图片中取出**其中一张**。

- `index`：要取第几张
  - `0` = 第一张
  - `1` = 第二张
  - `-1` = 最后一张
- `none_when_missing`：
  - `True`：索引越界时返回空结果
  - `False`：索引越界时直接报错

适合：
- 从 batch 中选出一张图片继续处理
- 做按索引取图的工作流

## 简单示例

### 单张图片

```text
https://example.com/image.png
```

```text
s3://my-bucket/path/to/image.png
```

```text
./input/example.png
```

### 批量图片

```text
https://example.com/a.png
https://example.com/b.png
https://example.com/c.png
```

## S3 说明

S3 使用 `boto3` 和 AWS 默认凭证链，也支持环境变量：

```bash
AWS_ENDPOINT_URL=http://127.0.0.1:9000
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_SESSION_TOKEN=...
```

`AWS_ENDPOINT_URL` 可用于 MinIO 或其他 S3 兼容存储。

## 开源协议

本项目使用 [MIT License](./LICENSE)。
