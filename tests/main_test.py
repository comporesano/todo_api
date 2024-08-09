import pytest
import requests

@pytest.fixture
def cookies():
    response = requests.post(
        'http://localhost:8000/auth/jwt/login',
        data='grant_type=password&username=1&password=1&scope=&client_id=string&client_secret=string',
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    cookie = str(response.cookies).split(' ')[1]
    response.raise_for_status() 
    return cookie

def test_create_task(cookies):
    headers = {
        'Cookie': cookies
    }
    response = requests.post(
        'http://localhost:8000/create-task/',
        params={"title": "Test Task", "description": "Test Description", "priority": "urgent"},
        headers=headers
    )
    assert response.status_code == 200
    assert "data" in response.json()

def test_grant_privilege(cookies):
    headers = {
        'Cookie': cookies
    }
    response = requests.post(
        'http://localhost:8000/grant/',
        params={"task_id": 1, "target_user_id": 2, "read": True, "edit": True},
        headers=headers
    )
    assert response.status_code == 200
    assert "data" in response.json()

def test_get_task(cookies):
    headers = {
        'Cookie': cookies
    }
    response = requests.get(
        'http://localhost:8000/task/1/get',
        headers=headers
    )
    assert response.status_code == 200
    assert "data" in response.json()

def test_edit_task(cookies):
    headers = {
        'Cookie': cookies
    }
    response = requests.post(
        'http://localhost:8000/task/1/edit',
        params={"title": "Updated Task", "description": "Updated Description"},
        headers=headers
    )
    assert response.status_code == 200
    assert "data" in response.json()

def test_full_scenario(cookies):
    test_create_task(cookies)
    test_grant_privilege(cookies)
    test_get_task(cookies)
    test_edit_task(cookies)
