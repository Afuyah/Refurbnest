from app import create_app, db  
from app.admin.models import User, Role 
from werkzeug.security import generate_password_hash
import getpass

# Create the Flask app
app = create_app()

def create_admin_user():
    with app.app_context():  # Ensure app context is active
        # Create the database tables if they don't exist
        db.create_all()

        # Create the 'Admin' role if it doesn't exist
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            admin_role = Role(name='Admin', description='Administrator role with full access')
            db.session.add(admin_role)
            db.session.commit()
            print("Admin role created successfully.")
        else:
            print("Admin role already exists.")

        # Create the admin user if they don't exist
        admin_user = User.query.filter_by(username='jhsync').first()
        if not admin_user:
            # Prompt for a secure password
            password = getpass.getpass('Enter a secure password for the admin user: ')

            # Create and add the admin user
            admin_user = User(
                username='jhsync',
                email='jhsync@gmail.com',
                role_id=admin_role.id  # Assign admin role
            )
            admin_user.set_password(password)  # Set the hashed password
            
            try:
                db.session.add(admin_user)
                db.session.commit()
                print("Admin user created successfully.")
            except Exception as e:
                db.session.rollback()  # Rollback in case of an error
                print(f"Error occurred while creating user: {e}")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    create_admin_user()
