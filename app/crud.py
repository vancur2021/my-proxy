import redis
import os
from contextlib import contextmanager

# 从环境变量获取 Redis 连接信息，提供默认值
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
PROXY_KEY = "proxies"

@contextmanager
def get_redis_client():
    """
    提供一个 Redis 客户端连接的上下文管理器。
    这确保了连接在使用后会被正确处理。
    """
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        yield client
    except redis.RedisError as e:
        print(f"!!! Could not connect to Redis: {e} !!!")
        yield None

def add_single_proxy(proxy: str, latency: int, redis_key: str = PROXY_KEY):
    """
    将单个有效代理添加到指定的 Redis Sorted Set Key。
    """
    with get_redis_client() as client:
        if client:
            try:
                client.zadd(redis_key, {proxy: latency})
            except redis.RedisError as e:
                print(f"!!! Redis Error while adding single proxy to {redis_key}: {e} !!!")

def add_proxies(proxies_with_latency: list[tuple[str, int]]):
    """
    将一批带有延迟分数的有效代理添加到 Redis Sorted Set。
    """
    if not proxies_with_latency:
        return
    
    mapping = {proxy: latency for proxy, latency in proxies_with_latency}
    
    with get_redis_client() as client:
        if client:
            try:
                added_count = client.zadd(PROXY_KEY, mapping)
                print(f"Successfully added/updated {added_count} proxies in Redis.")
            except redis.RedisError as e:
                print(f"!!! Redis Error while adding proxies: {e} !!!")

def get_best_proxy() -> str | None:
    """
    从 Redis 中获取延迟最低（分数最高）的代理。
    """
    with get_redis_client() as client:
        if client:
            try:
                # ZRANGE 0 0 获取分数最低的第一个代理
                best_proxies = client.zrange(PROXY_KEY, 0, 0)
                if best_proxies:
                    return best_proxies[0]
            except redis.RedisError as e:
                print(f"!!! Redis Error while getting best proxy: {e} !!!")
    return None

def get_all_proxies() -> list[str]:
    """
    获取所有可用的代理 IP。
    """
    with get_redis_client() as client:
        if client:
            return client.zrange(PROXY_KEY, 0, -1)
    return []

def count_proxies() -> int:
    """
    计算当前可用的代理 IP 数量。
    """
    with get_redis_client() as client:
        if client:
            return client.zcard(PROXY_KEY)
    return 0

def delete_proxy(proxy: str) -> int:
    """
    从 Redis 中删除指定的单个代理 IP。
    返回被删除的数量 (0 或 1)。
    """
    with get_redis_client() as client:
        if client:
            try:
                return client.zrem(PROXY_KEY, proxy)
            except redis.RedisError as e:
                print(f"!!! Redis Error while deleting proxy: {e} !!!")
    return 0

def remove_proxies(proxies: set[str]):
    """
    从 Redis 中批量移除指定的代理 IP。
    """
    if not proxies:
        return
    with get_redis_client() as client:
        if client:
            try:
                removed_count = client.zrem(PROXY_KEY, *proxies)
                print(f"Successfully removed {removed_count} invalid proxies.")
            except redis.RedisError as e:
                print(f"!!! Redis Error while removing proxies: {e} !!!")
