from fastapi import FastAPI, HTTPException
from . import crud, scheduler

app = FastAPI(
    title="Proxy IP Pool",
    description="一个用于获取、验证和提供代理 IP 的服务。",
    version="1.0.0",
)

@app.on_event("startup")
def startup_event():
    """
    应用启动时，初始化并启动定时任务。
    """
    scheduler.setup_scheduler()

@app.get("/get", tags=["Proxy"], summary="获取一个高质量代理")
def get_random_proxy():
    """
    从代理池中返回一个低延迟的可用代理 IP。
    """
    proxy = crud.get_best_proxy()
    if proxy:
        return {"proxy": proxy}
    raise HTTPException(status_code=404, detail="No available proxies")

@app.get("/all", tags=["Proxy"], summary="获取所有代理")
def get_all_proxies():
    """
    返回当前代理池中所有可用的代理 IP 列表。
    """
    proxies = crud.get_all_proxies()
    return {"proxies": proxies}

@app.get("/count", tags=["Proxy"], summary="获取代理总数")
def get_proxy_count():
    """
    返回当前代理池中可用代理 IP 的总数。
    """
    count = crud.count_proxies()
    return {"count": count}

@app.get("/", tags=["Root"], summary="服务健康检查")
def read_root():
    """
    根路径，用于简单的服务健康检查。
    """
    return {"status": "running"}
