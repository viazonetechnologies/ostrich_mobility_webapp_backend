import time
import threading
from typing import Any, Optional

class WebappCache:
    def __init__(self, default_ttl=180):  # 3 minutes default for webapp
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.cache_lock:
            if key in self.cache:
                item = self.cache[key]
                if time.time() < item['expires']:
                    return item['value']
                else:
                    del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        with self.cache_lock:
            self.cache[key] = {
                'value': value,
                'expires': time.time() + ttl
            }
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        with self.cache_lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self) -> None:
        """Clear all cache"""
        with self.cache_lock:
            self.cache.clear()
    
    def cleanup_expired(self) -> None:
        """Remove expired items"""
        current_time = time.time()
        with self.cache_lock:
            expired_keys = [
                key for key, item in self.cache.items()
                if current_time >= item['expires']
            ]
            for key in expired_keys:
                del self.cache[key]

# Global cache instance
webapp_cache = WebappCache()

def cache_key(prefix: str, *args) -> str:
    """Generate cache key"""
    return f"webapp:{prefix}:{'_'.join(map(str, args))}"