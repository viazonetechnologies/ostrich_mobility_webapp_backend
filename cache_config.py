from functools import wraps
from flask import jsonify
import time

cache = {}

def cache_response(timeout=60):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = f.__name__
            now = time.time()
            if key in cache and now - cache[key]['time'] < timeout:
                return jsonify(cache[key]['data'])
            result = f(*args, **kwargs)
            if result.status_code == 200:
                cache[key] = {'data': result.get_json(), 'time': now}
            return result
        return wrapper
    return decorator

def clear_cache_pattern(pattern):
    keys_to_delete = [k for k in cache.keys() if pattern in k]
    for k in keys_to_delete:
        del cache[k]
