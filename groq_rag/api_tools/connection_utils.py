
from langchain.memory.simple import SimpleMemory
import redis


redis_client = redis.StrictRedis(
    host='172.17.0.2', port=6379, db=0, decode_responses=True)
redis_client.set("session_expired", int(False))  # Store as 0


# Initialize memory to store session_id
memory = SimpleMemory(memories={
    # Initially, set to True to ensure login is called first
    "db": "postgres",
    "username": "",
    "password": ""
})
