from flask import render_template, redirect, url_for, flash, request,Blueprint 
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.admin.models import User, Role
from .forms import LoginForm, AdminUserForm,RegisterForm

from werkzeug.security import generate_password_hash
from functools import wraps


auth_bp = Blueprint('auth', __name__)

# Custom decorator for role-based access
def roles_required(*roles):
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login'))
            if not current_user.role.name in roles:
                flash('You do not have the required permissions to access this page.', 'danger')
                return redirect(url_for('main.home'))
            return func(*args **kwargs)
        return decorated_view
    return wrapper

# Home route
@auth_bp.route('/')
def home():
    return render_template('home.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        # Get the default role for a new user
        default_role = Role.query.filter_by(name='User').first()  # Assuming 'User' is the default role
        
        if default_role is None:
            flash('Default role does not exist. Please contact the admin.', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User(username=form.username.data,
                    email=form.email.data,
                    password_hash=generate_password_hash(form.password.data),
                    role_id=default_role.id)  # Assign the default role
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html', form=form)

# Logout route
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))

# Admin: Add a new user route (only admins can access)
@auth_bp.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
@roles_required('Admin')  # Only accessible by Admins
def add_user():
    form = AdminUserForm()
    form.set_role_choices()  # Populate roles dynamically
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password, role_id=form.role.data)
        db.session.add(new_user)
        db.session.commit()
        flash('New user added successfully!', 'success')
        return redirect(url_for('main.admin_dashboard'))
    
    return render_template('admin/add_user.html', form=form)

# Admin: View all users (Admin only)
@auth_bp.route('/admin/users')
@login_required
@roles_required('Admin')
def view_users():
    users = User.query.all()
    return render_template('admin/view_users.html', users=users)

# Admin dashboard (admin only)
@auth_bp.route('/admin')
@login_required
@roles_required('Admin')
def admin_dashboard():
    return render_template('admin/dashboard.html')




