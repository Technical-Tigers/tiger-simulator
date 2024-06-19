import redis.asyncio as redis

global redisPool
redisPool = redis.ConnectionPool.from_url('redis://localhost:6379/0')


# Importing and using it directly is not adviced
def open_redis_connection() -> redis.Redis:
    return redis.Redis(connection_pool=redisPool)


class RedisConnection(object):

    def __init__(self):
        pass

    async def __aenter__(self):
        self.redis = open_redis_connection()
        return self.redis

    async def __aexit__(self, *args):
        await self.redis.close()
