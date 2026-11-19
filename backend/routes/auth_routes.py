from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from model import db, User, StudentProfile

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data.get('username') or not data.get('password'):
        return jsonify({"status": "error", "message": "Username and password are required"}), 400

    user = User.query.filter_by(username=data['username']).first()

    if user and check_password_hash(user.password, data['password']):
        if user.status != 'Active':
            return jsonify({"status": "error", "message": "Account is inactive"}), 403

        access_token = create_access_token(identity=str(user.id), additional_claims={'role': user.role})
        profile = user.examiner_profile or user.student_profile
        return jsonify({ 'status': 'success', 'message': 'Login successful', 'access_token': access_token, 'role': user.role, 'name': profile.name if profile else user.username})
        
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401


@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"message": "No data provided"}), 400

    for field in ('username', 'email', 'password', 'name'):
        if not str(data.get(field, '')).strip():
            return jsonify({"message": f"{field} is required"}), 400

    if len(data['password']) < 6:
        return jsonify({"message": "Password must be at least 6 characters"}), 400

    user = User.query.filter_by(username=data['username']).first()

    if user:
        return jsonify({"message": "User already exists"}), 409

    user = User(
        username=data['username'],
        email=data['email'],
        password=generate_password_hash(data['password']),
        role='student'
    )
    user.student_profile = StudentProfile(name=data['name'],
                                      contact_details=data.get('contact_details'),
                                      department=data.get('department'))

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201


@auth_bp.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():

    user = User.query.get(get_jwt_identity())
    profile = user.examiner_profile or user.student_profile

    return jsonify({
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'name': profile.name if profile else user.username,
        'contact_details': profile.contact_details if profile else None,
        'department': profile.department if profile else None
    })


@auth_bp.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():

    user = User.query.get(get_jwt_identity())
    profile = user.examiner_profile or user.student_profile

    data = request.get_json()

    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)

    if profile:
        profile.name = data.get('name', profile.name)
        profile.contact_details = data.get('contact_details', profile.contact_details)
        profile.department = data.get('department', profile.department)

    if data.get('new_password'):
        if not check_password_hash(user.password, data.get('current_password', '')):
            return jsonify({"message": "Current password is incorrect"}), 400
        if len(data['new_password']) < 6:
            return jsonify({"message": "Password must be at least 6 characters"}), 400
        user.password = generate_password_hash(data['new_password'])

    db.session.commit()

    return jsonify({"message": "Profile updated successfully"})
