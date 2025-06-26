import time
import logging
from typing import Optional, Any
import redis

class Store:
    def __init__(self, host='localhost', port=6379, db=0,
                 reconnect_attempts=3, reconnect_delay=0.1,
                 connect_timeout=1, read_timeout=1):
        self.host = host
        self.port = port
        self.db = db
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self._client = None
        self._connect()

    def _connect(self):
        for attempt in range(self.reconnect_attempts):
            try:
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    socket_timeout=self.connect_timeout,
                    socket_connect_timeout=self.connect_timeout
                )
                self._client.ping()
                return
            except (redis.ConnectionError, redis.TimeoutError) as e:
                if attempt == self.reconnect_attempts - 1:
                    raise
                time.sleep(self.reconnect_delay)
                logging.warning(f"Connection attempt {attempt + 1} failed, retrying...")

    def _execute_with_retry(self, func, *args, **kwargs):
        for attempt in range(self.reconnect_attempts):
            try:
                return func(*args, **kwargs)
            except (redis.ConnectionError, redis.TimeoutError) as e:
                if attempt == self.reconnect_attempts - 1:
                    raise
                time.sleep(self.reconnect_delay)
                self._connect()
                logging.warning(f"Operation failed, retrying... (attempt {attempt + 1})")
                return None
        return None

    def get(self, key: str) -> Optional[Any]:
        try:
            return self._execute_with_retry(self._client.get, key)
        except (redis.ConnectionError, redis.TimeoutError):
            return None

    def cache_get(self, key: str) -> Optional[Any]:
        try:
            return self._execute_with_retry(
                self._client.get,
                f"cache:{key}",
                timeout=self.read_timeout
            )
        except (redis.ConnectionError, redis.TimeoutError):
            return None

    def cache_set(self, key: str, value: Any, expire: int = 60) -> bool:
        try:
            return bool(self._execute_with_retry(
                self._client.setex,
                f"cache:{key}",
                expire,
                value,
                timeout=self.read_timeout
            ))
        except (redis.ConnectionError, redis.TimeoutError):
            return False

    def set(self, key: str, value: Any) -> bool:
        try:
            return bool(self._execute_with_retry(self._client.set, key, value))
        except (redis.ConnectionError, redis.TimeoutError):
            return False