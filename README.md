# Proxy IP Pool

## 1. 项目概述

本项目旨在构建一个高效、稳定的代理 IP 池服务。它会定期从指定的源获取免费代理 IP，通过有效性验证和速度排序后，存入 Redis 数据库，并对外提供简单易用的 API 接口。

## 2. 核心功能

- **定时获取**: 每隔 20 分钟，从源地址 `https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt` 获取最新的代理 IP 列表。
- **有效性验证**: 使用 `https://quote.eastmoney.com/` 作为目标 URL，验证代理 IP 的可用性。
- **数据存储**: 将通过验证的有效代理 IP 存入 Redis，并根据响应延迟（ping 值）进行排序。存储时进行去重操作。
- **定时清理**: 每隔 5 分钟，重新验证 Redis 中的所有代理 IP，并自动剔除失效的 IP。
- **API 服务**: 提供 RESTful API 接口，用于：
    - 随机获取一个可用的代理 IP。
    - 获取所有可用的代理 IP 列表。
    - 统计当前可用的代理 IP 总数。

## 3. 技术选型

- **编程语言**: Python 3.9+
- **Web 框架**: FastAPI - 用于构建高性能的 API 服务。
- **HTTP 客户端**: httpx - 支持异步请求，用于高效验证代理。
- **数据库**: Redis - 用于高速缓存和存储代理 IP 列表。
- **定时任务**: APScheduler - 用于管理定时获取和清理任务。
- **依赖管理**: Poetry 或 Pipenv/Pip + requirements.txt

## 4. 项目结构

```
my-proxies/
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI 应用主入口
│   ├── crud.py         # Redis 数据读写操作
│   ├── scheduler.py    # 定时任务模块
│   └── validator.py    # 代理 IP 验证模块
├── .env                # 环境变量配置 (例如 Redis 连接信息)
├── .gitignore          # Git 忽略文件
├── pyproject.toml      # 项目依赖与配置 (使用 Poetry)
└── README.md           # 项目说明文档
```

## 5. API 接口设计

- `GET /proxy/random`
  - **功能**: 随机返回一个可用的代理 IP。
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

- `GET /proxy/all`
  - **功能**: 返回所有可用的代理 IP 列表。
  - **成功响应 (200 OK)**:
    ```json
    {
      "proxies": [
        "http://84.17.47.150:9002",
        "socks4://192.104.242.158:4145"
      ]
    }
    ```

- `GET /proxy/count`
  - **功能**: 返回当前可用代理 IP 的总数。
  - **成功响应 (200 OK)**:
    ```json
    {
      "count": 2
    }
    ```

## 6. 开发步骤

1.  **环境搭建**: 初始化 Python 项目，安装 FastAPI, Redis, httpx, APScheduler 等依赖。
2.  **Redis 操作封装**: 编写 `crud.py`，实现代理 IP 的增、删、查、去重和排序逻辑。
3.  **代理验证模块**: 编写 `validator.py`，实现单个及批量代理 IP 的有效性及速度检测功能。
4.  **定时任务模块**: 编写 `scheduler.py`，创建“定时获取”和“定时清理”两个核心任务。
5.  **API 接口实现**: 编写 `main.py`，创建 FastAPI 应用，并实现定义的三个 API 接口。
6.  **整合与测试**: 将所有模块整合，编写单元测试或进行手动测试，确保系统稳定运行。
## 7. 部署 (使用 Docker Compose)

本项目推荐使用 Docker Compose 进行一键部署，它会同时启动应用服务和 Redis 数据库。

1.  **确保 Docker 已安装**: 请确保你的系统中已经安装了 Docker 和 Docker Compose。

2.  **启动服务**: 在项目根目录下，执行以下命令：
    ```bash
    docker-compose up --build
    ```
    该命令会构建应用的 Docker 镜像并启动所有服务。如果需要后台运行，可以添加 `-d` 参数。

3.  **访问服务**: 服务启动后，可以通过 `http://localhost:8000` 访问 API。例如 `http://localhost:8000/docs` 查看 API 文档。

4.  **停止服务**:
    ```bash
    docker-compose down
    ```

## 8. 开发步骤 (新)

1.  **环境准备**: 创建 `Dockerfile`, `docker-compose.yml` 和 `requirements.txt` 文件。
2.  **启动开发环境**: 使用 `docker-compose up` 启动基础服务 (如 Redis)。
3.  **编写应用代码**:
    -   **Redis 操作封装**: 编写 `app/crud.py`。
    -   **代理验证模块**: 编写 `app/validator.py`。
    -   **定时任务模块**: 编写 `app/scheduler.py`。
    -   **API 接口实现**: 编写 `app/main.py`。
4.  **整合与测试**: 在 Docker 环境中进行完整的功能测试。
