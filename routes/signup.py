from flask import Flask, jsonify, request

app = Flask(__name__)

# Mock database
users = {}
todos = []



def create_account():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    if username in users:
        return jsonify({"error": "Username already exists"}), 400

    users[username] = {"password": password, "todos": []}
    return jsonify({"message": f"Account created for {username}"}), 201
