from flask import Flask, jsonify, request
from model import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import jwt_required, JWTManager, create_access_token
from flask_cors import CORS

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret'

jwt = JWTManager()
jwt.init_app(app)

CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db.init_app(app)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data.get('password')):
        access_token = create_access_token(identity=str(user.id), additional_claims={'role': user.role})
        return jsonify({ 'status': 'success', 'message': 'Login successful', 'access_token': access_token})
        
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"})

    user = User.query.filter_by(username=data['username']).first()
    if user:
        return jsonify({"status": "error", "message": "User already exists"})

    user = User(username=data['username'],email=data['email'],password=generate_password_hash(data['password']))
    db.session.add(user)
    db.session.commit()
    return jsonify({"status": "success", "message": "User created successfully"})

@app.route('/api/data', methods=['GET'])
@jwt_required()
def get_data():
    data = {
            "status" : "success", 
            "message": "Hello, world!"
            }
    return jsonify(data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username= 'admin',email= 'admin@gmail.com',password=generate_password_hash('1111'), role= 'admin')
            db.session.add(admin)
            db.session.commit()
    app.run(debug = True)