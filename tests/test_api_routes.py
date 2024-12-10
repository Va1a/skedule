import pytest
from skedule import create_app, db, bcrypt
from skedule.models import User, Shift, Day, Assignment
from datetime import datetime
import json
from flask_login import login_user

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(app, client):
    # Create test user with hashed password
    hashed_pw = bcrypt.generate_password_hash('test_password').decode('utf-8')
    user = User(
        name='Test User',
        email='test@test.com',
        phone='1234567890',
        password=hashed_pw,
        external_id='99',
        oauth_id='test_oauth_id'
    )
    db.session.add(user)
    db.session.commit()
    
    # Login directly using Flask-Login instead of through the endpoint
    with app.test_request_context():
        login_user(user)
        
    return {}

def test_api_shift(app, client, auth_headers):
    day = Day(name='Test Day', date=datetime.now().date())
    db.session.add(day)
    db.session.commit()
    
    shift = Shift(
        name='Test Shift',
        startTime=datetime.now(),
        duration=400,
        maxEmployees=3,
        minEmployees=1,
        day_id=day.id
    )
    db.session.add(shift)
    db.session.commit()

    # Test getting shift
    response = client.get(f'/api/shift/{shift.id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Test Shift'
    assert data['maxEmployees'] == 3

def test_api_assignment(app, client, auth_headers):
    user = User.query.filter_by(email='test@test.com').first()
    day = Day(name='Test Day', date=datetime.now().date())
    db.session.add(day)
    db.session.commit()
    
    shift = Shift(
        name='Test Shift',
        startTime=datetime.now(),
        duration=400,
        maxEmployees=3,
        minEmployees=1,
        day_id=day.id
    )
    db.session.add(shift)
    db.session.commit()

    assignment = Assignment(user=user, shift=shift)
    db.session.add(assignment)
    db.session.commit()

    # Test getting assignment
    response = client.get(f'/api/assignment/{assignment.id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['user'] == user.id
    assert data['shift'] == shift.id
