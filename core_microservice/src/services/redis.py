from redis import Redis
from src.settings import app_config
import json

class RedisService:

    def __init__(self, host=app_config.REDIS_HOST, port=app_config.REDIS_PORT):
        self.redis = Redis(host=host, port=port, db=0)


    def load_session(self, session_id: str) -> dict:
        data = self.redis.get(f"session:{session_id}")
        if data:
            return json.loads(data)
        return {}


    def save_session(self, session_id: str, data: dict, expire: int) -> None:
        if data:
            self.redis.setex(
                f"session:{session_id}",
                expire,
                json.dumps(data)
            )
        else:
            self.redis.delete(f"session:{session_id}")


redis_service = RedisService()