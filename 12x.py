from app import create_app, db
from app.admin.models import User, Role
from werkzeug.security import generate_password_hash
import getpass

# Create the Flask app
app = create_app()

def create_roles_and_admin():
    with app.app_context():  # Ensure app context is active
        # Create the database tables if they don't exist
        db.create_all()

        # Check if 'User' role exists, if not, create it
        user_role = Role.query.filter_by(name='User').first()
        if not user_role:
            user_role = Role(name='User', description='Default user role')
            db.session.add(user_role)
            print("User role created successfully.")
        else:
            print("User role already exists.")

        # Check if 'Admin' role exists, if not, create it
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            admin_role = Role(name='Admin', description='Administrator role with full access')
            db.session.add(admin_role)
            print("Admin role created successfully.")
        else:
            print("Admin role already exists.")

        # Commit the changes for roles creation
        db.session.commit()

        # Prompt for admin details (username, email, password)
        username = input('Enter a username for the admin user: ')
        email = input('Enter an email for the admin user: ')
        password = getpass.getpass('Enter a secure password for the admin user: ')

        # Check if the admin user already exists
        admin_user = User.query.filter_by(username=username).first()
        if not admin_user:
            try:
                # Create and add the admin user
                admin_user = User(
                    username=username,
                    email=email,
                    role_id=admin_role.id  # Assign admin role
                )
                admin_user.set_password(password)  # Set the hashed password

                db.session.add(admin_user)
                db.session.commit()
                print("Admin user created successfully.")
            except Exception as e:
                db.session.rollback()  # Rollback in case of an error
                print(f"Error occurred while creating user: {e}")
        else:
            print(f"Admin user '{username}' already exists.")

if __name__ == '__main__':
    create_roles_and_admin()
