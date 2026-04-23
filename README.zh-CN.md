# ComfyUI Load Image From Data URL

[English README](./README.md)

这是一个用于 ComfyUI 的开源自定义节点集合，支持从 URL、本地路径、S3 加载图片，也支持批量加载和批量选择。

Batch 加载节点使用可通过 `+ Add URI` 按钮添加的独立 URI 输入框，不再按逗号或换行拆分同一个字符串，因此可以安全处理包含任意 payload 文本的 data URL。

## 包含的节点

- `Load Image From URI`（`LoadImageFromURI`）
- `Load Image From URI (Batch)`（`LoadImageFromURIBatch`）
- `Load Image From URI (List)`（`LoadImageFromURIList`）
- `Load Image Selector (Batch)`（`LoadImageSelectorBatch`）
- `Load Image Selector (List)`（`LoadImageSelectorList`）

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

更新节点后也需要刷新浏览器页面，确保 ComfyUI 加载用于 Batch `+ Add URI` 按钮的前端扩展。

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
- `uri_missing`：URI 为空时如何处理
  - `None`：image/mask 返回 `None`
  - `Placeholder`：返回 ComfyUI 兼容的空 tensor
  - `Throw error`：直接报错

适合：
- 加载单张网络图片
- 加载单张本地图片
- 加载单张 S3 图片

### Load Image From URI (Batch)

这个节点用于把**多张图片加载为一个 batch tensor**。

- 点击 `+ Add URI`，为每张图片添加一个独立 URI/路径输入框
- 其他参数含义与单图节点相同
- 空 URI item 会按 `uri_missing` 处理；`None` 会在 batch 输出中跳过该项，`Placeholder` 会用空 tensor 保留该位置，`Throw error` 会直接报错。
- `size_mode`：
  - `pad_to_max`：输出一个 batch tensor，将较小图片和 mask 补边到最大宽高
  - `resize_to_first`：输出一个 batch tensor，将后续图片和 mask 缩放到第一张图片尺寸
  - `error`：任意图片尺寸不一致时直接报错

适合：
- 把多张图片送入支持 batch 输入的节点
- 强制输出单个 batch tensor

### Load Image From URI (List)

这个节点用于加载**多张图片并保留每张图片的原始分辨率**。

- 点击 `+ Add URI`，为每张图片添加一个独立 URI/路径输入框
- 输出 ComfyUI 图片 / mask 列表
- 不缩放、不补边
- 空 URI item 会按 `uri_missing` 处理；`None` 会在该 list item 输出 `None`，`Placeholder` 会输出空 tensor，`Throw error` 会直接报错。

### Load Image Selector (Batch)

这个节点用于从 `Load Image From URI (Batch)` 的 batch tensor 中取出**其中一张**。

- `index`：要取第几张
  - `0` = 第一张
  - `1` = 第二张
  - `-1` = 最后一张
- `image_missing`：选中的 image 缺失时如何处理
- `mask_missing`：选中的 mask 缺失时如何处理
  - `None`：该输出返回 `None`
  - `Placeholder`：该输出返回 ComfyUI 兼容的空 tensor
  - `Throw error`：直接报错
- `image` 和 `mask` 都是可选输入，并且会分别按各自策略处理。
- `index` 越界时，`image` 和 `mask` 都视为缺失。

适合：
- 从 batch tensor 中选出一张图片继续处理
- 做按索引取图的工作流

### Load Image Selector (List)

这个节点用于从 `Load Image From URI (List)` 的 ComfyUI 图片列表中取出**其中一张**，并保持选中图片的原始分辨率。

输入参数与 `Load Image Selector (Batch)` 一致，但它会一次性接收完整列表，并按 list index 选择。

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

使用 `+ Add URI` 按钮添加多个输入框，并把每个 URI 单独填入一个输入框。每个 URI 输入框后都有独立的 `Remove` 按钮，删除后剩余输入会重新连续编号。

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
