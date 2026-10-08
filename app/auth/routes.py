from bson import ObjectId
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.auth.forms import RegisterForm, LoginForm
from app.models.user import User
#el import of profile class is to make sure enu el acc is not deleted before login
#check if account is deleted and email/pass are correct then login
from app.models.profile import Profile
from app.auth.decorators import login_required
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# Blueprint for web-based (session) authentication
auth_bp = Blueprint('auth', __name__)

# Blueprint for API-based (JWT) authentication
auth_api_bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')

limiter = Limiter(get_remote_address, default_limits=["10 per minute"])

# --- Web Routes (Session-Based) ---

@auth_bp.route('/register', methods=['GET', 'POST'])
#@login_required
@limiter.limit("10 per minute")
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data

        db = current_app.db
        if User.find_by_email(email, db):
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        User.create(first_name, last_name, email, password, db)
        flash('Registration successful!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password_input = form.password.data

        db = current_app.db
        user = User.find_by_email(email, db)
        if user and User.verify_password(user['password'], password_input):
            session['user_id'] = str(user['_id'])
            flash('Login successful!', 'success')
            return redirect(url_for('auth.home'))
        

        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template("auth/dashboard.html", user=session['user'])
    return redirect(url_for('auth.login'))

@auth_bp.route('/home')
@login_required
def home():
    db = current_app.db

    user = User.get_by_id(session['user_id'], db)

    return render_template(
        "auth/dashboard.html",
        user=user
    )

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    session.pop('user_id', None)
    flash('You have been logged out. ', 'success')
    return redirect(url_for('auth.login'))

# --- API Routes (JWT-Based) ---

@auth_api_bp.route('/register', methods=['POST'])
def api_register():
    data = request.json

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    password = data.get("password")

    db = current_app.db
    if User.find_by_email(email, db):
        return jsonify({"error": "Email already registered"}), 400
    user_id = User.create(first_name, last_name, email, password, db)

    return jsonify({"message": "User registered successfully", "user_id": str(user_id)}), 201

@auth_api_bp.route('/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get("email")
    password_input = data.get("password")
    #user_id = data.get("user_id")

    db = current_app.db
    user = User.find_by_email(email, db)
    #user.get("deleted", False): el false hye el default lal deleted eza mwjode aw la, ka feild, mch ka value ela
    if user and User.verify_password(user['password'], password_input) and not user.get("deleted", False):
        access_token = create_access_token(identity=str(user["_id"]))
        return jsonify({"message": "Login successful", "access_token": access_token}), 200
    print("profile is deleted")
    if not user:
        return jsonify({"error":"Account doesn't exist"}), 404
    if not User.verify_password(user['password'], password_input):
        return jsonify({"error": "Incorrect password"}), 401
    if user.get("deleted", False):
        return jsonify({"error":"Account has been deleted"}), 403
    #return jsonify({"error": "Invalid email or password"}), 401

@auth_api_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected_route():
    current_user_id = get_jwt_identity()

    db = current_app.db

    user = db.users.find_one({
        "_id": ObjectId(current_user_id)
    })

    print("CURRENT USER ID:", current_user_id)
    print("USER:", user)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        #"message": "Welcome!",
        "user_id": current_user_id,
        "first_name": user.get("first_name", "")
    }), 200

'''
@auth_api_bp.route('/protected', methods=['GET'])
@jwt_required() 
def protected_route():
    current_user_id = get_jwt_identity()
    db = current_app.db
    user = db.users.find_one({
        "_id": ObjectId(current_user_id)
    })

    return jsonify({"message": "Welcome!", "user_id": current_user_id ,  "first_name": user.get("first_name", "")}), 200
'''

'''
    line 12 dashboard.html

    <h1 class="display-5 fw-bold">
                    <!-- i class="fas fa-tachometer-alt text-danger me-3"></i>
                    Welcome, {{ user.first_name }}!
                </h1 -->
'''
