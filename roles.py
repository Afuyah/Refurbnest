from app import db
from app.admin.models import Role

# Add default roles if they don't exist
if not Role.query.filter_by(name='User').first():
    user_role = Role(name='User')
    db.session.add(user_role)

if not Role.query.filter_by(name='Admin').first():
    admin_role = Role(name='Admin')
    db.session.add(admin_role)

db.session.commit()
