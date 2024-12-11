from skedule import create_app, db, bcrypt
from skedule.models import User, Assignment, Shift
app = create_app()
ctx = app.app_context()
ctx.push()
password = 'test'
hashedpw = bcrypt.generate_password_hash(password).decode('utf-8')
u = User(id=1, name='Vala Skedule', email='vala@skedule.net', phone='8185551234', password=hashedpw)
u1 = User(id=2, name='Sam Sepiol', email='sam@skedule.net', phone='8183224172', password=hashedpw)
u2 = User(id=3, name='Dolores Haze', email='haze@skedule.net', phone='8052123644', password=hashedpw)
db.session.add(u)
db.session.add(u1)
db.session.add(u2)
# print(u.toJSON())
db.session.commit()