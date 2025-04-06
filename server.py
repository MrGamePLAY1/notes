from flask import Flask, request, jsonify, render_template, redirect, url_for
import json
from flask_pymongo import PyMongo
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from datetime import datetime
from flask import session
import secrets
secrets.token_hex(16)  # This will generate a 32-character hex strin

# Load environment variables
load_dotenv()


app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)

# Use the key from .env, with a fallback for development
app.secret_key = os.environ.get("SECRET_KEY")

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
    print("\n=== SESSION DEBUG ===")
    print(f"Session contents: {session}")
    user = None
    if 'user_id' in session:
        # Getting the details from the mongoDB
        user = mongo.db.users.find_one({"_id": ObjectId(session['user_id'])})
        print(user)
    else:
        print("User not logged in")
    
    return render_template("index.html", user=user)

@app.route("/notes")
def notes():
    
    print("\n=== SESSION DEBUG ===")
    print(f"Session contents: {session}")
    
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's notes from database
    try:
        user_id = session['user_id']
        user_notes = list(mongo.db.notes.find({"user_id": user_id, "isArchived": False}).sort("updatedAt", -1))
        
        # Convert ObjectId to string for each note
        for note in user_notes:
            note['_id'] = str(note['_id'])
        
        return render_template("notes.html", notes=user_notes, user_id=user_id)
    except Exception as e:
        print(f"Error retrieving notes: {e}")
        return render_template("notes.html", notes=[], error="Failed to load notes")
    
@app.route("/api/notes")
def api_notes():
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        user_id = session['user_id']
        user_notes = list(mongo.db.notes.find({"user_id": user_id, "isArchived": False}).sort("updatedAt", -1))
        
        # Convert ObjectId to string for each note
        for note in user_notes:
            note['_id'] = str(note['_id'])
            # Convert datetime objects to ISO format strings for JSON serialization
            note['createdAt'] = note['createdAt'].isoformat()
            note['updatedAt'] = note['updatedAt'].isoformat()
        
        return jsonify({"notes": user_notes})
    except Exception as e:
        print(f"Error retrieving notes: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/account")
def account():
    if 'user_id' in session:
        # Getting the details from the mongoDB
        user = mongo.db.users.find_one({"_id": ObjectId(session['user_id'])})
        username = user["username"]
        email = user["email"]
        return render_template("account.html", user=user)
    else:
        print("User not logged in")
        return redirect(url_for('login'))

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
    error = None
    
    # Handle form submission
    if request.method == "POST":
        try:
            email = request.form.get("email")
            password = request.form.get("password")
            
            # Basic validation
            if not email or not password:
                error = "Please fill in all fields"
                return render_template("login.html", error=error)
            
            # Get the users collection
            users = mongo.db.users
            
            # Find user by email
            user = users.find_one({"email": email})
            
            # Check credentials
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
                
                print(f"User logged in: {user['username']} ({user['email']})")
                print(f"Session after login: {session}")
                
                # Redirect to notes page
                return redirect(url_for("notes"))
            else:
                error = "Invalid email or password"
                print(f"Failed login attempt for email: {email}")
        
        except Exception as e:
            print(f"Login error: {e}")
            error = "An error occurred. Please try again."
    
    # For GET requests or failed logins, show the login form
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    # Clear the session data
    session.clear()
    print("User logged out, session cleared")
    # Redirect to the home page
    return redirect(url_for('index'))

# Handling notes which are saved
@app.route("/save-note", methods=["POST"])
def save_note():
# Check if user is logged in
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "You must be logged in to save notes"})
    
    try:
        # Get JSON data from request
        data = request.get_json()
        user_id = session['user_id']
        
        print(f"Received note data: {data}")
        
        # Basic validation
        if not data or not data.get('title'):
            return jsonify({"success": False, "error": "Note title is required"})
        
        # For a new note
        if data.get('_id') == 'new':
            # Create new note document
            new_note = {
                "user_id": user_id,
                "title": data.get('title'),
                "content": data.get('content', ''),
                "color": data.get('color', '#ffffff'),
                "isPinned": False,
                "isArchived": False,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now()
            }
            
            # Insert into MongoDB
            result = mongo.db.notes.insert_one(new_note)
            note_id = str(result.inserted_id)
            
            print(f"Created new note with ID: {note_id}")
            
            # Get the complete note for response
            saved_note = mongo.db.notes.find_one({"_id": result.inserted_id})
            note_response = {
                "_id": str(saved_note["_id"]),
                "title": saved_note["title"],
                "content": saved_note["content"],
                "color": saved_note.get("color", "#ffffff"),
                "isPinned": saved_note.get("isPinned", False),
                "isArchived": saved_note.get("isArchived", False),
                "createdAt": saved_note["createdAt"].isoformat(),
                "updatedAt": saved_note["updatedAt"].isoformat()
            }
            
            return jsonify({
                "success": True,
                "note_id": note_id,
                "note": note_response,
                "message": "Note created successfully"
            })
            
        # For updating an existing note
        else:
            try:
                note_id = ObjectId(data.get('_id'))
                
                # Verify the note belongs to this user
                existing_note = mongo.db.notes.find_one({
                    "_id": note_id,
                    "user_id": user_id
                })
                
                if not existing_note:
                    return jsonify({"success": False, "error": "Note not found or unauthorized"})
                
                # Update the note
                result = mongo.db.notes.update_one(
                    {"_id": note_id},
                    {"$set": {
                        "title": data.get('title'),
                        "content": data.get('content', ''),
                        "color": data.get('color', existing_note.get('color', '#ffffff')),
                        "updatedAt": datetime.now()
                    }}
                )
                
                if result.modified_count == 0 and result.matched_count == 0:
                    return jsonify({"success": False, "error": "Failed to update note"})
                
                # Get the updated note for response
                updated_note = mongo.db.notes.find_one({"_id": note_id})
                note_response = {
                    "_id": str(updated_note["_id"]),
                    "title": updated_note["title"],
                    "content": updated_note["content"],
                    "color": updated_note.get("color", "#ffffff"),
                    "isPinned": updated_note.get("isPinned", False),
                    "isArchived": updated_note.get("isArchived", False),
                    "createdAt": updated_note["createdAt"].isoformat(),
                    "updatedAt": updated_note["updatedAt"].isoformat()
                }
                
                print(f"Updated note with ID: {data.get('_id')}")
                
                return jsonify({
                    "success": True,
                    "note": note_response,
                    "message": "Note updated successfully"
                })
                
            except Exception as e:
                print(f"Error updating note: {e}")
                return jsonify({
                    "success": False, 
                    "error": f"Invalid note ID or format: {str(e)}"
                })
            
    except Exception as e:
        print(f"Error saving note: {e}")
        return jsonify({"success": False, "error": str(e)})

    
        

@app.route("/signup", methods=["GET", "POST"])
def signup():
    # For GET requests, show the signup form
    if request.method == "GET":
        return render_template("signup.html")
    
    # For POST requests, process the form submission
    try:
        print("Form data received:", request.form)
        
        # Basic validation
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not username or not email or not password:
            error = "Please fill in all required fields."
            print(f"Missing required fields: {username=}, {email=}, {password=}")
            return render_template("signup.html", error=error)
        
        # Get the users collection from the database
        users = mongo.db.users
        
        # Check if user exists
        existing_user = users.find_one({
            "$or": [
                {"username": username},
                {"email": email}
            ]
        })
        
        if existing_user:
            print(f"User already exists: {existing_user['username']}, {existing_user['email']}")
            error = "User with this username or email already exists"
            return render_template("signup.html", error=error)
        
        # Hash password and create user
        hashed_password = generate_password_hash(password)
        
        # Create new user document
        new_user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "createdAt": datetime.now(),
            "isActive": True
        }
        
        
        print("Creating new user:", new_user)
        
        # Insert the user into the database
        result = users.insert_one(new_user)
        
        if not result.inserted_id:
            print("Failed to insert user into database")
            error = "Database error occurred. Please try again."
            return render_template("signup.html", error=error)
        
        # Get the inserted ID from the result
        user_id = result.inserted_id
        print(f"User created with ID: {user_id}")
        
        # Setting the session variables
        session["user_id"] = str(user_id) 
        session["username"] = username
        
        print(f"Session after signup: {session}")
        
        # Crwate a new note for the user
        try: 
            sampe_note = {
                "user_id": str(user_id),
                "title": "Welcome to IdeaVault!",
                "content": "This is your first note. You can edit or delete it, or create new notes.\n\n" +
                        "## Markdown is supported\n\n" +
                        "* You can create lists\n" +
                        "* Format **bold** and *italic* text\n" +
                        "* Add [links](https://example.com)\n\n" +
                        "Enjoy organizing your ideas!",
                "tags": ["welcome", "getting-started"],
                "color": "#e8f5e9",  # Light green color
                "isPinned": True,
                "isArchived": False,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now()
            }
            
            result = mongo.db.notes.insert_one(sampe_note)
            
            if result.inserted_id:
                print(f"Sample note created for user {username} with ID: {result.inserted_id}")
            else:
                print("Failed to create sample note")
                    
        except Exception as e:
                print(f"Error creating sample note: {e}")
                # Continue with signup even if sample note creation fails
        
        
        # Redirect to notes page
        return redirect(url_for('notes'))
        
    except Exception as e:
        print(f"Error creating user: {e}")
        error = "An error occurred during signup. Please try again."
        return render_template("signup.html", error=error)





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