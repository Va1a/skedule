from skedule import create_app, db, bcrypt
from skedule.models import User, Assignment, Shift
app = create_app()
ctx = app.app_context()
ctx.push()
password = 'test'
hashedpw = bcrypt.generate_password_hash(password).decode('utf-8')
u = User(id=1, name='Vala Bahrami', email='vala@ucsb.edu', phone='8185551234', password=hashedpw)
db.session.add(u)
# print(u.toJSON())
db.session.commit()