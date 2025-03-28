from flask import Flask, request, jsonify, render_template, redirect, url_for
import json
from flask_pymongo import PyMongo
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from datetime import datetime
from flask import session




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
    # check if the user is logged in 
    user = None
    if 'user_id' in session:
        # Getting the details from the mongoDB
        user = mongo.db.users.find_one({"_id": ObjectId(session['user_id'])})
        print(user)
    
    return render_template("index.html", user=user)

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
@app.route("/login")
def login():
    error = None
    return render_template("login.html", error=error)

# API auth login endpoint
@app.route("/api/auth/login", methods=["POST"])
def api_login():
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        email = data.get("email")
        password = data.get("password")
        
        # Basic validation
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Get the users collection from the database
        users = mongo.db.users
        
        # Find the user by email
        user = users.find_one({"email": email})
        
        # Check if user exists and password is correct
        if user and check_password_hash(user["password"], password):
            # Store user info in session
            session["user_id"] = str(user["_id"])
            session["username"] = user["username"]
            session["email"] = user["email"]
            
            # Update last login time
            users.update_one(
                {"_id": user["_id"]},
                {"$set": {"lastLogin": datetime.now()}}
            )
            
            # Return user data (excluding password)
            user_data = {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "isActive": user.get("isActive", True),
                "createdAt": user.get("createdAt").isoformat() if "createdAt" in user else None
            }
            
            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": user_data
            })
        else:
            # Invalid credentials
            return jsonify({
                "success": False,
                "error": "Invalid email or password"
            }), 401
                
    except Exception as e:
        print(f"API login error: {e}")
        return jsonify({
            "success": False,
            "error": "An error occurred during login"
        }), 500

# Signup page
@app.route("/signup", methods=["GET"])
def signup_page():
    return render_template("signup.html")

# Handling notes which are saved
@app.route("/save-note", methods=["POST"])
def save_note():
    # Chcking if the user is currently logged in
    if 'user_id' not in session:
        alert = "You must be logged in to save notes"
        return redirect(url_for('login', alert=alert))

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