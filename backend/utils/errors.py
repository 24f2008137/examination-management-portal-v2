import json
import re

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException

from model import db


def _error(message, status):
    return jsonify({'message': message}), status


def register_error_handlers(app):
    """Turn exceptions into JSON responses instead of HTML / bare 500s.

    All error bodies use the same shape as the rest of the API:
        {"message": "..."}
    JWT errors are left to flask-jwt-extended (they keep their {"msg": ...} shape).
    """
    @app.before_request
    def require_json_object():
        if request.method in ('POST', 'PUT', 'PATCH') and request.is_json and request.content_length:
            try:
                body = json.loads(request.get_data(as_text=True))
            except ValueError:
                return  # malformed JSON: get_json() raises a 400 that the handler below formats
            if not isinstance(body, dict):
                return _error('Request body must be a JSON object', 400)

    # --- HTTP errors (404, 405, 400 bad JSON, 415, and wrapped 500s) --------
    FRIENDLY = {
        400: 'Invalid or malformed request body',
        415: 'Content-Type must be application/json',
        500: 'Internal server error',
    }

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        response = e.get_response()          # keeps headers such as Allow on a 405
        response.data = json.dumps({'message': FRIENDLY.get(e.code, e.description)})
        response.content_type = 'application/json'
        return response

    # --- missing field: data['username'] ------------------------------------
    @app.errorhandler(KeyError)
    def handle_key_error(e):
        field = e.args[0] if e.args else 'unknown'
        app.logger.warning('Missing field %r on %s %s', field, request.method, request.path)
        return _error(f'Missing required field: {field}', 400)

    # --- bad value: datetime.strptime(...), int('abc') ----------------------
    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return _error(f'Invalid value: {e}', 400)

    # --- database constraint violations -------------------------------------
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        db.session.rollback()
        detail = str(getattr(e, 'orig', e))

        unique = re.search(r'UNIQUE constraint failed: (.+)', detail)
        if unique:
            cols = [c.split('.')[-1] for c in unique.group(1).split(', ')]
            if len(cols) == 1:
                return _error(f'{cols[0]} already exists', 409)
            return _error(f"This combination of {', '.join(cols)} already exists", 409)

        not_null = re.search(r'NOT NULL constraint failed: (?:\w+\.)?(\w+)', detail)
        if not_null:
            if request.method == 'DELETE':
                # deleting a parent makes SQLAlchemy try to NULL the children's foreign key
                return _error('Cannot delete: other records depend on this item', 409)
            return _error(f'{not_null.group(1)} is required', 400)

        return _error('Operation conflicts with existing data', 409)

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(e):
        db.session.rollback()
        app.logger.exception('Database error on %s %s', request.method, request.path)
        return _error('Database error', 500)