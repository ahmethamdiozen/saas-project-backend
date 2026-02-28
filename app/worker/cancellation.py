import threading

class JobCancelledError(Exception):
    pass

class CancellationToken:
    def __init__(self):
        self.cancelled = False
        self.__lock = threading.Lock()

    def cancel(self):
        with self.__lock:
            self.__cancelled = True
    
    def is_cancelled(self):
        with self.__lock:
            return self.cancelled
        
    def raise_if_cancelled(self):
        if self.is_cancelled():
            raise JobCancelledError("Job cancelled")
        

_active_tokens = {}
_registry_lock = threading.Lock()

def register_token(job_id: str, token: CancellationToken):
    with _registry_lock:
        _active_tokens[job_id] = token

def unregister_token(job_id: str):
    with _registry_lock:
        _active_tokens.pop(job_id, None)

def cancel_token(job_id: str):
    with _registry_lock:
        token = _active_tokens.get(job_id)
        if token:
            token.cancel()

