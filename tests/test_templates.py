import pytest
from bs4 import BeautifulSoup
from app import app, db, User, Poll, PollOption
from werkzeug.security import generate_password_hash
from flask_login import login_user

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3306/POLLyverse?charset=utf8mb4'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    app.config['SERVER_NAME'] = 'localhost'  # Set server name for url generation
    
    with app.test_client() as client:
        with app.app_context():
            # Drop all tables and recreate them
            db.drop_all()
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def test_user(client):
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(user)
        db.session.commit()
        return user

def login_test_user(client, test_user):
    with app.app_context():
        client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        # Ensure the user is logged in for the session
        login_user(test_user)

def test_landing_page_structure(client):
    """Test the structure of the landing page"""
    response = client.get('/')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check main heading
    assert soup.find('h1', string='Create & Share Polls Instantly') is not None
    
    # Check for registration and login links
    nav = soup.find('nav')
    assert nav is not None
    assert nav.find('a', string='Register') is not None
    assert nav.find('a', string='Login') is not None

def test_login_page_structure(client):
    """Test the structure of the login page"""
    response = client.get('/login')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check form elements
    form = soup.find('form', {'method': 'POST'})
    assert form is not None
    
    # Check input fields
    assert soup.find('input', {'name': 'username'}) is not None
    assert soup.find('input', {'name': 'password'}) is not None
    assert soup.find('button', {'type': 'submit'}) is not None

def test_create_poll_page_structure(client, test_user):
    """Test the structure of the create poll page"""
    # Login first
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    
    response = client.get('/create')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check form elements
    form = soup.find('form', {'method': 'POST'})
    assert form is not None
    
    # Check input fields
    assert soup.find('input', {'name': 'title'}) is not None
    assert soup.find('textarea', {'name': 'description'}) is not None
    assert soup.find('button', {'type': 'submit'}) is not None

def test_flash_messages_rendering(client):
    """Test if flash messages are properly rendered"""
    # First request to initialize the session
    client.get('/')
    
    # Set flash message
    with client.session_transaction() as session:
        session['_flashes'] = [('info', 'Test message')]
    
    # Second request to check if flash message is rendered
    response = client.get('/')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    flash_message = soup.find('div', class_='alert-info')
    assert flash_message is not None, "Flash message div not found"
    assert 'Test message' in flash_message.text, "Flash message text not found"

def test_navigation_when_logged_in(client, test_user):
    """Test navigation elements when user is logged in"""
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    
    response = client.get('/')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    nav = soup.find('nav')
    
    # Check that logged-in specific links are present
    assert soup.find('a', {'class': 'dropdown-toggle'}) is not None
    assert soup.find('a', {'class': 'dropdown-item'}, string='Logout') is not None
    
    # Check that login/register links are not present
    assert soup.find('a', {'class': 'nav-link', 'href': '/login'}) is None
    assert soup.find('a', {'class': 'nav-link', 'href': '/register'}) is None 