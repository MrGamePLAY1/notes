from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()


app = Flask(__name__, 
    template_folder='../../templates',
    static_folder='../../static'
)

try:
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
    print("MONGO_URI found in environment variables")
except KeyError:
    raise KeyError("MONGO_URI not found in environment variables")


mongo = PyMongo(app)

# Home/index page
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/notes")
def notes():
    return render_template("notes.html")

# Terms of Service page
@app.route("/terms")
def terms():
    return render_template("terms.html")

# Privacy Policy page
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Handle login logic here
        pass
    return render_template("login.html")

# Signup page
@app.route("/signup", methods=["GET"])
def signup_page():
    return render_template("signup.html")

# Handle signup form submission
@app.route("/signup", methods=["POST"])
def signup():
    try:
        # Get the users collection from the database
        users = mongo.db.users
        
        # Check if user exists
        existing_user = users.find_one({
            "$or": [
                {"username": request.form["username"]},
                {"email": request.form["email"]}
            ]
        })
        
        if existing_user:
            return "User with this username or email already exists"
        
        # Hash password and create user
        hashed_password = generate_password_hash(request.form["password"])
        users.insert_one({
            "username": request.form["username"],
            "email": request.form["email"],
            "password": hashed_password,
            "createdAt": datetime.now(),
            "isActive": True
        })
        
        print(f"User created with ID: {users.inserted_id}")
        return redirect(url_for('login'))
    except Exception as e:
            print(f"Error creating user: {e}")
            return "An error occurred during signup. Please try again."



# Testing
@app.route("/test-db")
def test_db():
    try:
        # Try to get the list of collections in the database
        collections = mongo.db.list_collection_names()
        
        # Try to count documents in the users collection
        user_count = mongo.db.users.count_documents({})
        
        return {
            "status": "success",
            "message": "MongoDB connection successful",
            "collections": collections,
            "user_count": user_count,
            "database": mongo.db.name
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    app.run(debug=True)