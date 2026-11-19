from functools import wraps

from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from model import ExaminerProfile, StudentProfile


def roles_required(*roles):
    """Require a valid JWT whose 'role' claim is one of `roles`.

    Replaces the repeated:
        @jwt_required()
        ...
        if get_jwt().get('role') != 'admin':
            return jsonify({"message": "Access denied"}), 403
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            if get_jwt().get('role') not in roles:
                return jsonify({'message': 'Access denied'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def _profile_required(role, model, label):
    """Role check + load the caller's profile and pass it to the view.

    The profile is injected as a keyword argument named after the role
    ('examiner' or 'student'), so views declare it in their signature.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            profile = model.query.filter_by(
                user_id=int(get_jwt_identity())
            ).first()

            if not profile:
                return jsonify({'message': f'{label} profile not found'}), 404

            kwargs[role] = profile
            return fn(*args, **kwargs)

        return roles_required(role)(wrapper)
    return decorator


# Usage:  @examiner_required  ->  def view(examiner): ...
examiner_required = _profile_required('examiner', ExaminerProfile, 'Examiner')
student_required = _profile_required('student', StudentProfile, 'Student')