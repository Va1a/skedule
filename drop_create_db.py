from cso import create_app, db
app = create_app()
ctx = app.app_context()
ctx.push()
db.drop_all()
db.create_all()
ctx.pop()
