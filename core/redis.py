import redis
import os
import redis

redis_client = redis.Redis(
    host="redis-12288.c82.us-east-1-2.ec2.cloud.redislabs.com",
    port=12288,
    password="ZsaN1QjhBcoO3BQI36QVo4rmw8OvIAQF",
    decode_responses=True,
    ssl=False  # <--- important
)

try:
    redis_client.ping()
    print(redis_client.ping())
    print("Redis Connected Successfully")
except Exception as e:
    print("Redis Connection Error:", e)