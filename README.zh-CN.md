# ComfyUI Load Image From Data URL

[English README](./README.md)

这是一个轻量级的开源 ComfyUI 自定义节点，用于从多种 URI 来源加载图片，并输出标准的 ComfyUI `IMAGE` 与 `MASK` 张量。

## 功能特性

- 支持 `data:` URL（base64 和 URL 编码两种数据格式）
- 支持通过 `boto3` 读取 `s3://` URI
- 支持远程 URL：`http://`、`https://`、`ftp://`
- 支持 `file://` URL
- 支持本地文件路径（绝对路径、相对路径、Windows 盘符路径）
- 输出：
  - `IMAGE`：形状 `[1, H, W, C]`，`float32`，数值范围 `0~1`
  - `MASK`：形状 `[1, H, W]`，`float32`
    - 输入图像有 alpha 通道时：`mask = 1 - alpha`
    - 输入图像无 alpha 通道时：返回全 0 mask
- 远程请求使用 Python 标准库 `urllib`（不依赖 `requests`）
- 可限制远程与 S3 下载大小，避免无上限占用内存

## 仓库结构

- `__init__.py`：节点实现与 ComfyUI 节点注册
- `requirements.txt`：Python 依赖列表

## 运行依赖

- ComfyUI 对应的 Python 环境
- 已安装并可运行的 ComfyUI
- Python 包：
  - `numpy`
  - `torch`
  - `Pillow`
  - `boto3`（当前仓库中已声明）

在 ComfyUI 使用的 Python 环境中安装依赖：

```bash
pip install -r requirements.txt
```

## 安装方式

将本仓库克隆或复制到 ComfyUI 的 `custom_nodes` 目录：

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/qq1014853731/ComfyUI-Load-Image-From-Data-Url.git
```

然后重启 ComfyUI。

## 节点信息

- **节点类名**：`LoadImageFromURI`
- **显示名称**：`Load Image From URI`
- **分类**：`image`
- **输入参数**：
  - `uri`（`STRING`，支持多行）：URI / URL / 本地路径
  - `timeout`（`INT`，默认 `0`，范围 `0~600`）：远程请求超时时间（秒）。设置为 `0` 表示不显式设置超时。
  - `max_download_bytes`（`INT`，默认 `0`）：HTTP/FTP/S3 下载大小上限，单位为字节。设置为 `0` 表示不限制大小。
- **输出参数**：
  - `image`（`IMAGE`）
  - `mask`（`MASK`）

## 使用示例

### 1）Data URL（base64 PNG）

```text
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
```

### 2）远程 URL

```text
https://example.com/image.png
```

### 3）S3 URI

```text
s3://my-bucket/path/to/image.png
```

S3 访问基于 `boto3` 的默认凭证链，并支持通过环境变量覆盖。

凭证 / 端点生效顺序：

1. 节点显式参数
2. 环境变量
3. AWS 默认凭证提供链

常用环境变量：

```bash
AWS_ENDPOINT_URL=http://127.0.0.1:9000
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_SESSION_TOKEN=...
```

说明：

- `timeout` 输入会应用到 S3 连接超时和读取超时。
- `max_download_bytes` 输入会应用到 HTTP/FTP/S3 响应体读取。
- 可通过 `AWS_ENDPOINT_URL` 连接 MinIO 或其他 S3 兼容存储服务。
- 若未显式提供凭证，`boto3` 会回退到 profile / 实例角色 / 默认链。
- S3 object key 会进行 URL 解码，所以 `s3://bucket/a%20b.png` 会读取 key `a b.png`。

### 4）本地文件路径

```text
/Users/yourname/Pictures/sample.png
```

相对路径会基于 ComfyUI 进程的当前工作目录解析。

Windows 示例：

```text
C:\Users\yourname\Pictures\sample.png
```

### 5）File URL

```text
file:///Users/yourname/Pictures/sample.png
```

## 错误处理

该节点会针对常见输入问题抛出明确错误，包括：

- `uri` 为空或不是字符串
- 不支持的 URI scheme
- `data:` URL 格式不合法
- 本地文件不存在或路径不是文件
- S3 对象读取失败（路径无效、权限不足、对象不存在等）
- 远程 HTTP/URL 拉取失败
- 图片解码失败

## 贡献方式

欢迎提交 Issue 和 Pull Request。

建议在反馈中包含：

- 清晰的问题描述
- 复现步骤（如果是 bug）
- 预期行为与实际行为
- 环境信息（操作系统、Python、ComfyUI 版本）

## 开源协议

本项目使用 [MIT License](./LICENSE) 开源。
