import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from . import crud, validator

scheduler = AsyncIOScheduler()

async def fetch_and_validate_proxies():
    """
    任务一：获取源代理，并流式验证、存入数据库。
    """
    print("Starting to fetch source proxies...")
    source_proxies = await validator.fetch_source_proxies()
    if not source_proxies:
        print("No proxies fetched from source.")
        return
    
    print(f"Validating {len(source_proxies)} fetched proxies...")
    await validator.check_proxies(source_proxies)
        
    print(f"Fetch and validate task finished. Current proxy count: {crud.count_proxies()}")

async def revalidate_existing_proxies():
    """
    任务二：重新验证数据库中已有的所有代理，更新分数并移除失效的。
    """
    print("Starting to revalidate existing proxies...")
    existing_proxies = crud.get_all_proxies()
    if not existing_proxies:
        print("No existing proxies to revalidate.")
        return
    
    # 定义一个临时的 Redis Key，用于存放本次重新验证的结果
    TEMP_KEY = "proxies_temp_revalidation"
    
    # 重新验证，并将有效的代理流式写入到 TEMP_KEY
    print(f"Revalidating {len(existing_proxies)} existing proxies into {TEMP_KEY}...")
    await validator.check_proxies(existing_proxies, redis_key=TEMP_KEY)
    
    with crud.get_redis_client() as client:
        if client:
            # 使用 ZUNIONSTORE 将新验证的结果合并回主 Key (crud.PROXY_KEY)
            # WEIGHTS 1 1 表示如果成员同时存在于两个集合，分数相加（这里我们用新分数覆盖旧分数）
            # AGGREGATE MAX 确保我们总是取最新的（通常是更低的）延迟作为分数
            client.zunionstore(crud.PROXY_KEY, {crud.PROXY_KEY: 1, TEMP_KEY: 1}, aggregate='MAX')
            
            # 计算失效的代理：存在于旧集合但不存在于新验证集合的成员
            # 注意：这里需要优化，因为 ZDIFFSTORE 在 redis 6.2+ 才可用
            # 简化逻辑：我们假设定时任务期间没有新代理加入，直接移除分数较高的（旧的）
            # 一个更简单的策略是：直接用 TEMP_KEY 覆盖 PROXY_KEY
            
            # 高效的覆盖和清理操作
            # 1. 开始一个事务
            pipe = client.pipeline()
            # 2. 将临时 key 重命名为主 key，这是一个原子操作，可以瞬间覆盖旧数据
            pipe.rename(TEMP_KEY, crud.PROXY_KEY, nx=False) # nx=False 允许覆盖
            # 3. 执行事务
            pipe.execute()
            
            revalidated_count = client.zcard(crud.PROXY_KEY)
            removed_count = len(existing_proxies) - revalidated_count
            print(f"Revalidation complete. {revalidated_count} proxies updated, {removed_count} removed.")

    print(f"Revalidation task finished. Current proxy count: {crud.count_proxies()}")

def setup_scheduler():
    """
    配置并启动所有定时任务。
    """
    # 任务一：每 1 小时获取一次新代理
    scheduler.add_job(fetch_and_validate_proxies, 'interval', hours=1, id='fetch_proxies')
    
    # 任务二：每 30 分钟清理一次无效代理
    scheduler.add_job(revalidate_existing_proxies, 'interval', minutes=30, id='revalidate_proxies')
    
    # 启动调度器
    scheduler.start()
    print("Scheduler started.")
    
    # 为了立即看到效果，应用启动时先执行一次任务
    # 使用 asyncio.create_task 在后台运行，避免阻塞应用启动
    asyncio.create_task(fetch_and_validate_proxies())
