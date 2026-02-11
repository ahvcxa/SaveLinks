import pytest
import os
from src.service.link_service import LinkService
from src.database.repository import LinkRepository
from src.core.exceptions import ValidationError, SaveLinksError

@pytest.fixture
def service():
    # Use an in-memory database for testing
    repo = LinkRepository(db_path=":memory:")
    return LinkService(repo)

def test_register_login(service):
    username = "testuser"
    password = "password123"
    
    # Register
    assert service.register_user(username, password) is True
    
    # Login
    user_id, key = service.login_user(username, password)
    assert user_id is not None
    assert key is not None

def test_login_invalid_password(service):
    service.register_user("user2", "pass")
    with pytest.raises(ValidationError):
        service.login_user("user2", "wrongpass")

def test_add_search_link(service):
    service.register_user("user3", "pass")
    user_id, key = service.login_user("user3", "pass")
    
    service.add_link(user_id, key, "Python", "https://python.org")
    
    results = service.search_links(user_id, key, "python")
    assert len(results) == 1
    assert results[0]['topic'] == "Python"
    assert results[0]['link'] == "https://python.org"

def test_search_no_results(service):
    service.register_user("user4", "pass")
    user_id, key = service.login_user("user4", "pass")
    
    results = service.search_links(user_id, key, "java")
    assert len(results) == 0

def test_delete_link(service):
    service.register_user("user5", "pass")
    user_id, key = service.login_user("user5", "pass")
    service.add_link(user_id, key, "Delete Me", "url")
    
    results = service.search_links(user_id, key, "Delete Me")
    link_id = results[0]['id']
    
    service.delete_link(user_id, link_id)
    
    results_after = service.search_links(user_id, key, "Delete Me")
    assert len(results_after) == 0
