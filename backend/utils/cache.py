"""Redis caching for the EMP API.

* ``@cached(namespace, ttl)`` caches the JSON body of a successful GET view.
* Every key lives under ``emp:cache:<namespace>:...`` and carries a TTL
  (cache expiry), so stale data can never live forever.
* Cache invalidation is automatic: a SQLAlchemy session hook watches which
  models were written in a transaction and, after the commit succeeds,
  deletes the namespaces that depend on them. Route code does not need to
  remember to clear anything.
* If Redis is down every helper silently degrades to "no cache" - the API
  keeps working, just slower.
"""
import json
import os
from functools import wraps

import redis
from flask import Response, request
from flask_jwt_extended import get_jwt, get_jwt_identity
from sqlalchemy import event
from sqlalchemy.orm import Session

PREFIX = 'emp:cache'

# TTLs in seconds (override with env vars if you like)
TTL_EXAMS = int(os.environ.get('CACHE_TTL_EXAMS', 120))
TTL_EXAM_DETAIL = int(os.environ.get('CACHE_TTL_EXAM_DETAIL', 300))
TTL_RUBRICS = int(os.environ.get('CACHE_TTL_RUBRICS', 600))
TTL_SLOTS = int(os.environ.get('CACHE_TTL_SLOTS', 60))
TTL_DASHBOARD = int(os.environ.get('CACHE_TTL_DASHBOARD', 60))

_client = None

def get_redis():
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
    return _client


# low-level helpers (never raise)
def cache_get(key):
    try:
        return get_redis().get(key)
    except redis.RedisError:
        return None


def cache_set(key, value, ttl):
    try:
        get_redis().set(key, value, ex=ttl)
    except redis.RedisError:
        pass


def invalidate(*namespaces):
    """Delete every cached entry that belongs to the given namespaces."""
    try:
        client = get_redis()
        for ns in namespaces:
            keys = list(client.scan_iter(match=f'{PREFIX}:{ns}:*', count=200))
            if keys:
                client.delete(*keys)
    except redis.RedisError:
        pass


def cached(namespace, ttl, per_user=False):
    """Cache a GET view's JSON response.

    The key always contains the URL path, the sorted query string and the
    caller's role (responses differ per role). ``per_user`` also adds the user
    id: pass ``True`` for all roles, or a tuple such as ``('examiner',)`` for
    only those roles - use it when the data is filtered to the logged-in user.

    Put it *below* ``@jwt_required()`` / ``@roles_required(...)`` so the role
    is already known, and only 200 responses are stored.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            role = get_jwt().get('role', '-')
            query = '&'.join(f'{k}={v}' for k, v in sorted(request.args.items()))
            wants_user = per_user is True or (isinstance(per_user, tuple) and role in per_user)
            user = f':u{get_jwt_identity()}' if wants_user else ''
            key = f'{PREFIX}:{namespace}:{request.path}?{query}:{role}{user}'

            hit = cache_get(key)
            if hit is not None:
                resp = Response(hit, mimetype='application/json')
                resp.headers['X-Cache'] = 'HIT'
                return resp, 200

            result = fn(*args, **kwargs)

            if isinstance(result, tuple) and len(result) >= 2 and result[1] == 200:
                body = result[0].get_data(as_text=True)
                cache_set(key, body, ttl)
                result[0].headers['X-Cache'] = 'MISS'
            elif not isinstance(result, tuple) and getattr(result, 'status_code', None) == 200:
                cache_set(key, result.get_data(as_text=True), ttl)
                result.headers['X-Cache'] = 'MISS'
            return result
        return wrapper
    return decorator


# model name -> cache namespaces that become stale when that model is written
MODEL_NAMESPACES = {
    'Course':          ('exams', 'dashboard'),
    'Exam':            ('exams', 'slots', 'rubrics', 'dashboard'),
    'ExamExaminer':    ('exams',),
    'ExamRubric':      ('rubrics',),
    'ExamSlot':        ('slots', 'dashboard'),
    'ExaminerProfile': ('slots', 'exams', 'dashboard'),
    'StudentProfile':  ('dashboard',),
    'Booking':         ('slots', 'dashboard'),
    'Evaluation':      ('dashboard',),
}


@event.listens_for(Session, 'after_flush')
def _collect_changed_models(session, flush_context):
    pending = session.info.setdefault('cache_namespaces', set())
    for obj in list(session.new) + list(session.dirty) + list(session.deleted):
        pending.update(MODEL_NAMESPACES.get(type(obj).__name__, ()))


@event.listens_for(Session, 'after_commit')
def _invalidate_after_commit(session):
    namespaces = session.info.pop('cache_namespaces', None)
    if namespaces:
        invalidate(*namespaces)


@event.listens_for(Session, 'after_rollback')
def _forget_after_rollback(session):
    session.info.pop('cache_namespaces', None)
