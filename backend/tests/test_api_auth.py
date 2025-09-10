"""
Test suite for authentication API endpoints.
Tests user registration, login, character naming, and authentication flows.
"""

import pytest
from fastapi import status
from app.core.auth import verify_password


@pytest.mark.unit
def test_user_registration_success(client, test_user_data):
    """Test successful user registration."""
    response = client.post("/auth/register", json={
        "username": test_user_data["username"],
        "age": test_user_data["age"],
        "password": test_user_data["password"]
    })
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["username"] == test_user_data["username"]
    assert data["user"]["age"] == test_user_data["age"]


@pytest.mark.unit
def test_user_registration_duplicate_username(client, test_user, test_user_data):
    """Test registration with duplicate username."""
    response = client.post("/auth/register", json={
        "username": test_user.username,  # Same username as existing user
        "age": 25,
        "password": "DifferentPass123!"
    })
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "already taken" in data["detail"].lower()


@pytest.mark.unit
def test_user_registration_invalid_username(client):
    """Test registration with invalid username (too short)."""
    response = client.post("/auth/register", json={
        "username": "ab",  # Too short (less than 3 characters)
        "age": 25,
        "password": "TestPass123!"
    })
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit
def test_user_registration_weak_password(client):
    """Test registration with weak password."""
    response = client.post("/auth/register", json={
        "username": "testuser",
        "age": 25,
        "password": "weak"  # Too short
    })
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit
def test_user_login_success(client, test_user):
    """Test successful user login."""
    response = client.post("/auth/login", json={
        "username": test_user.username,
        "password": test_user.plain_password
    })
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["username"] == test_user.username


@pytest.mark.unit
def test_user_login_invalid_username(client):
    """Test login with non-existent username."""
    response = client.post("/auth/login", json={
        "username": "nonexistentuser",
        "password": "SomePass123!"
    })
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "incorrect" in data["detail"].lower()


@pytest.mark.unit
def test_user_login_wrong_password(client, test_user):
    """Test login with wrong password."""
    response = client.post("/auth/login", json={
        "username": test_user.username,
        "password": "WrongPassword123!"
    })
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "incorrect" in data["detail"].lower()


@pytest.mark.unit
def test_get_current_user_authenticated(client, test_user, auth_headers):
    """Test getting current user info with valid token."""
    response = client.get("/auth/me", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user.email
    assert data["username"] == test_user.username
    assert data["ai_character_name"] == test_user.ai_character_name


@pytest.mark.unit
def test_get_current_user_unauthenticated(client):
    """Test getting current user info without token."""
    response = client.get("/auth/me")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.unit
def test_get_current_user_invalid_token(client):
    """Test getting current user info with invalid token."""
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"})
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.unit
def test_update_character_name_success(client, test_user, auth_headers):
    """Test successful AI character name update."""
    new_name = "Buddy"
    response = client.put("/auth/character-name", 
                         json={"character_name": new_name},
                         headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Character name updated successfully"
    assert data["character_name"] == new_name
    
    # Verify the change persisted
    user_response = client.get("/auth/me", headers=auth_headers)
    user_data = user_response.json()
    assert user_data["ai_character_name"] == new_name


@pytest.mark.unit
def test_update_character_name_unauthenticated(client):
    """Test character name update without authentication."""
    response = client.put("/auth/character-name", 
                         json={"character_name": "NewName"})
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.unit
def test_update_character_name_empty(client, auth_headers):
    """Test character name update with empty string."""
    response = client.put("/auth/character-name", 
                         json={"character_name": ""},
                         headers=auth_headers)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit
def test_update_character_name_too_long(client, auth_headers):
    """Test character name update with overly long name."""
    long_name = "A" * 101  # Assuming 100 char limit
    response = client.put("/auth/character-name", 
                         json={"character_name": long_name},
                         headers=auth_headers)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
def test_complete_auth_flow(client, test_user_data):
    """Test complete authentication flow from registration to character update."""
    # Step 1: Register
    register_response = client.post("/auth/register", json={
        "username": test_user_data["username"],
        "age": test_user_data["age"],
        "password": test_user_data["password"]
    })
    assert register_response.status_code == status.HTTP_201_CREATED
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Get user info
    user_response = client.get("/auth/me", headers=headers)
    assert user_response.status_code == status.HTTP_200_OK
    user_data = user_response.json()
    assert user_data["ai_character_name"] == "AI Assistant"  # Default
    
    # Step 3: Update character name
    character_response = client.put("/auth/character-name", 
                                   json={"character_name": "MyAI"}, 
                                   headers=headers)
    assert character_response.status_code == status.HTTP_200_OK
    
    # Step 4: Verify update
    final_response = client.get("/auth/me", headers=headers)
    final_data = final_response.json()
    assert final_data["ai_character_name"] == "MyAI"


@pytest.mark.integration 
def test_login_after_character_name_update(client, test_user, auth_headers):
    """Test that character name persists after login."""
    new_name = "PersistentAI"
    
    # Update character name
    client.put("/auth/character-name", 
               json={"character_name": new_name},
               headers=auth_headers)
    
    # Login again
    login_response = client.post("/auth/login", json={
        "username": test_user.username,
        "password": test_user.plain_password
    })
    
    # Check that character name is preserved
    assert login_response.status_code == status.HTTP_200_OK
    user_data = login_response.json()["user"]
    assert user_data["ai_character_name"] == new_name