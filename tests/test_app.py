import copy
import pytest
from httpx import AsyncClient, ASGITransport
from src.app import app, activities

pytestmark = pytest.mark.asyncio

# Keep a pristine copy of the in-memory DB to reset between tests
_original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test"""
    activities.clear()
    activities.update(copy.deepcopy(_original_activities))
    yield


@pytest.mark.asyncio
async def test_root_redirect():
    # Arrange
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Act
        response = await ac.get("/", follow_redirects=False)
    # Assert
    assert response.status_code in (307, 302)
    assert response.headers["location"].endswith("/static/index.html")


@pytest.mark.asyncio
async def test_get_activities():
    # Arrange
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Act
        response = await ac.get("/activities")
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data


@pytest.mark.asyncio
async def test_signup_for_activity():
    # Arrange
    test_email = "newstudent@mergington.edu"
    activity = "Chess Club"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Act
        response = await ac.post(f"/activities/{activity}/signup", params={"email": test_email})
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {test_email} for {activity}"


@pytest.mark.asyncio
async def test_unregister_from_activity():
    # Arrange
    test_email = "newstudent@mergington.edu"
    activity = "Chess Club"
    # First, ensure the student is signed up
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(f"/activities/{activity}/signup", params={"email": test_email})
        # Act
        response = await ac.post(f"/activities/{activity}/unregister", params={"email": test_email})
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {test_email} from {activity}"
