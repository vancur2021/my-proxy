import httpx
import asyncio
from httpx import AsyncHTTPTransport
from . import crud

# 验证代理的目标 URL 和超时设置
VALIDATION_URL = "https://quote.eastmoney.com/"
VALIDATION_TIMEOUT = 8  # seconds
MAX_CONCURRENCY = 100 # 最大并发数

async def validate_proxy(proxy: str, semaphore: asyncio.Semaphore, redis_key: str):
    """
    验证单个代理的可用性，如果有效，则直接写入指定的 Redis Key。
    """
    async with semaphore:
        try:
            transport = AsyncHTTPTransport(proxy=proxy)
            async with httpx.AsyncClient(transport=transport, timeout=VALIDATION_TIMEOUT) as client:
                start_time = asyncio.get_event_loop().time()
                response = await client.get(VALIDATION_URL)
                end_time = asyncio.get_event_loop().time()
                
                if response.status_code == 200:
                    latency = int((end_time - start_time) * 1000)  # 转换为毫秒
                    print(f"Proxy {proxy} is valid, latency: {latency}ms. Adding to {redis_key}...")
                    crud.add_single_proxy(proxy, latency, redis_key)
        except httpx.RequestError as e:
            print(f"Proxy {proxy} failed: {e.__class__.__name__}")
        except ValueError as e:
            # 捕获 httpx 不支持的代理类型, 例如 socks4
            print(f"Proxy {proxy} has unsupported type: {e}")

async def check_proxies(proxies: list[str], redis_key: str = crud.PROXY_KEY):
    """
    并发地检查一组代理，并将有效的代理写入指定的 Redis Key。
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [validate_proxy(proxy, semaphore, redis_key) for proxy in proxies]
    await asyncio.gather(*tasks)

async def fetch_source_proxies() -> list[str]:
    """
    从源 URL 获取代理列表。
    """
    url = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt"
    # url = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/countries/CA/data.txt"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=20)
            if response.status_code == 200:
                proxies = response.text.strip().split('\n')
                # 过滤掉 httpx 不支持的 socks4 代理
                filtered_proxies = [p for p in proxies if not p.startswith("socks4://")]
                print(f"Fetched {len(proxies)} proxies from source, {len(filtered_proxies)} after filtering socks4.")
                return filtered_proxies
            else:
                print(f"Failed to fetch proxies, status code: {response.status_code}")
                return []
    except httpx.RequestError as e:
        print(f"Error fetching source proxies: {e}")
        return []
