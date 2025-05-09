from functools import wraps
from flask import abort

def requires_db(db_uri):
    def requires_db_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if db_uri is None:
                abort(400)
            return f(*args, **kwargs)
        return wrapper
    return requires_db_decorator
