from flask import Flask, jsonify, request
from config import Config
from flask_sqlalchemy import SQLAlchemy
from services.pr_service import fetch_pr_from_github, analyze_pr_with_llm


import os

app = Flask(__name__)
app.config.from_object(Config)

# Set up SQLAlchemy for the PostgreSQL database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")  # your database URL from .env
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True)

# Define the Todo model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    is_done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Flask API!"})

# Create accounta
@app.route('/signup', methods=['POST'])
def create_account():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Create user in the database
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": f"Account created for {username}"}), 201

# Sign in
@app.route('/signin', methods=['POST'])
def access_account():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.password == password:
        return jsonify({"message": f"Welcome back, {username}!"})

    return jsonify({"error": "Invalid username or password"}), 401

# Add a todo
@app.route('/todo', methods=['POST'])
def add_todo():
    data = request.get_json()
    username = data.get('username')
    todo_title = data.get('todo')

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Create todo for the user
    todo = Todo(title=todo_title, user_id=user.id)
    db.session.add(todo)
    db.session.commit()
    return jsonify({"message": "Todo added successfully"})

# Get todos
@app.route('/todos', methods=['GET'])
def get_todos():
    username = request.args.get('username')

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    todos = Todo.query.filter_by(user_id=user.id).all()
    return jsonify({"todos": [todo.title for todo in todos]})

# Fetch PR from GitHub and give feedback using LLM
@app.route('/fetch-pr', methods=['GET'])
def fetch_pr():
    repo_url = request.args.get('repo_url')
    if not repo_url:
        return jsonify({"error": "Repository URL is required"}), 400

    pr_details = fetch_pr_from_github(repo_url)
    feedback = analyze_pr_with_llm(pr_details)

    return jsonify({"pr_details": pr_details, "feedback": feedback})

if __name__ == '__main__':
    app.run(debug=True)
