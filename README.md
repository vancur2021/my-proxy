# Proxy IP Pool

## 1. 项目概述

本项目旨在构建一个高效、稳定的代理 IP 池服务。它会定期从指定的源获取免费代理 IP，通过并发的有效性验证和速度排序后，存入 Redis 数据库，并对外提供简单易用的 API 接口。

## 2. 核心功能

- **定时获取**: 每隔 1 小时，从源地址获取最新的代理 IP 列表，并预先过滤掉 `socks4` 等不兼容的代理。
- **有效性验证**: 使用 `https://quote.eastmoney.com/` 作为目标 URL，通过一个可配置大小的并发池（例如，100个并发），高效地验证代理 IP 的可用性。
- **流式存储**: 代理一旦被验证为有效，会立即被存入 Redis，并根据其响应延迟（ping 值）进行排序，无需等待整个批次完成。
- **定时清理**: 每隔 30 分钟，重新验证 Redis 中的所有代理 IP，并自动、高效地剔除失效的 IP。
- **API 服务**: 提供 RESTful API 接口，用于：
    - 获取一个高质量（低延迟）的可用代理 IP。
    - 获取所有可用的代理 IP 列表。
    - 统计当前可用的代理 IP 总数。

## 3. 技术选型

- **编程语言**: Python 3.10+
- **Web 框架**: FastAPI - 用于构建高性能的 API 服务。
- **HTTP 客户端**: httpx - 支持异步请求，用于高效验证代理。
- **数据库**: Redis - 用于高速缓存和存储代理 IP 列表。
- **定时任务**: APScheduler - 用于管理定时获取和清理任务。
- **部署**: Docker / Docker Compose

## 4. 项目结构

```
my-proxies/
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI 应用主入口
│   ├── crud.py         # Redis 数据读写操作
│   ├── scheduler.py    # 定时任务模块
│   └── validator.py    # 代理 IP 验证模块
├── .gitignore          # Git 忽略文件
├── Dockerfile          # 应用的 Docker 镜像定义
├── docker-compose.yml  # Docker Compose 部署文件
├── requirements.txt    # Python 依赖列表
└── README.md           # 项目说明文档
```

## 5. API 接口设计

- `GET /get`
  - **功能**: 从延迟最低的前10个代理中随机返回一个，以实现负载均衡。
  - **成功响应 (200 OK)**:
    ```json
    {
      "proxy": "socks5://157.180.121.252:22759"
    }
    ```
  - **失败响应 (404 Not Found)**:
    ```json
    {
      "detail": "No available proxies"
    }
    ```

- `GET /all`
  - **功能**: 返回所有可用的代理 IP 列表。
  - **成功响应 (200 OK)**:
    ```json
    {
      "proxies": [
        "http://84.17.47.150:9002",
        "socks5://192.104.242.158:4145"
      ]
    }
    ```

- `GET /count`
  - **功能**: 返回当前可用代理 IP 的总数。
  - **成功响应 (200 OK)**:
    ```json
    {
      "count": 2
    }
    ```

- `DELETE /del`
  - **功能**: 删除一个指定的代理 IP。
  - **查询参数**: `proxy` (string, required) - 需要删除的代理地址，例如 `http://84.17.47.150:9002`。
  - **成功响应 (200 OK)**:
    ```json
    {
      "status": "success",
      "detail": "Proxy 'http://84.17.47.150:9002' deleted."
    }
    ```
  - **失败响应 (404 Not Found)**:
    ```json
    {
      "detail": "Proxy 'http://84.17.47.150:9002' not found."
    }
    ```

## 6. 部署 (使用 Docker Compose)

本项目推荐使用 Docker Compose 进行一键部署，它会同时启动应用服务和 Redis 数据库。

1.  **确保 Docker 已安装**: 请确保你的系统中已经安装了 Docker 和 Docker Compose。

2.  **启动服务**: 在项目根目录下，执行以下命令：
    ```bash
    docker-compose up --build
    ```
    该命令会构建应用的 Docker 镜像并启动所有服务。如果需要后台运行，可以添加 `-d` 参数。

3.  **访问服务**: 服务启动后，可以通过 `http://localhost:5010` 访问 API。例如 `http://localhost:5010/docs` 查看自动生成的 API 文档。

4.  **停止服务**:
    ```bash
    docker-compose down
