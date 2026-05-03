import uuid
import time
import threading

_sessions = {}
_SESSION_TTL = 30 * 60  # 30 minutes
_lock = threading.Lock()


def create_session(essay_text):
    session_id = str(uuid.uuid4())
    with _lock:
        _sessions[session_id] = {
            "essay_text": essay_text,
            "sections": None,
            "current_stage": "parsing",
            "results": {},
            "created_at": time.time(),
            "last_access": time.time(),
        }
    return session_id


def get_session(session_id):
    _cleanup_expired()
    with _lock:
        s = _sessions.get(session_id)
        if s:
            s["last_access"] = time.time()
        # Return a reference — callers must hold their own synchronization
        # if they intend to mutate. For this single-server app with the GIL,
        # simple dict key assignment is safe enough.
        return s


def set_sections(session_id, sections):
    _cleanup_expired()
    with _lock:
        s = _sessions.get(session_id)
        if s:
            s["last_access"] = time.time()
            s["sections"] = sections
            s["current_stage"] = "structure_confirmed"


def set_stage(session_id, stage):
    _cleanup_expired()
    with _lock:
        s = _sessions.get(session_id)
        if s:
            s["last_access"] = time.time()
            s["current_stage"] = stage


def add_result(session_id, stage, result):
    _cleanup_expired()
    with _lock:
        s = _sessions.get(session_id)
        if s:
            s["last_access"] = time.time()
            s["results"][stage] = result


def _cleanup_expired():
    now = time.time()
    with _lock:
        expired = [
            sid for sid, s in _sessions.items()
            if now - s["last_access"] > _SESSION_TTL
        ]
        for sid in expired:
            del _sessions[sid]
