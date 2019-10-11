import pytest
from fastapi import Depends, FastAPI
from starlette import status
from starlette.testclient import TestClient

from fastapi_users import FastAPIUsers
from fastapi_users.models import BaseUser, BaseUserDB


@pytest.fixture
def fastapi_users(mock_user_db, mock_authentication) -> FastAPIUsers:
    class User(BaseUser):
        pass

    return FastAPIUsers(mock_user_db, mock_authentication, User)


@pytest.fixture
def test_app_client(fastapi_users: FastAPIUsers) -> TestClient:
    app = FastAPI()
    app.include_router(fastapi_users.router)

    @app.get("/current-user")
    def current_user(user=Depends(fastapi_users.get_current_user)):
        return user

    @app.get("/current-active-user")
    def current_active_user(user=Depends(fastapi_users.get_current_active_user)):
        return user

    @app.get("/current-superuser")
    def current_superuser(user=Depends(fastapi_users.get_current_superuser)):
        return user

    return TestClient(app)


class TestRouter:
    def test_routes_exist(self, test_app_client: TestClient):
        response = test_app_client.post("/register")
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = test_app_client.post("/login")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestGetCurrentUser:
    def test_missing_token(self, test_app_client: TestClient):
        response = test_app_client.get("/current-user")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token(self, test_app_client: TestClient):
        response = test_app_client.get(
            "/current-user", headers={"Authorization": "Bearer foo"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_valid_token(self, test_app_client: TestClient, user: BaseUserDB):
        response = test_app_client.get(
            "/current-user", headers={"Authorization": f"Bearer {user.id}"}
        )
        assert response.status_code == status.HTTP_200_OK


class TestGetCurrentActiveUser:
    def test_missing_token(self, test_app_client: TestClient):
        response = test_app_client.get("/current-active-user")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token(self, test_app_client: TestClient):
        response = test_app_client.get(
            "/current-active-user", headers={"Authorization": "Bearer foo"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_valid_token_inactive_user(
        self, test_app_client: TestClient, inactive_user: BaseUserDB
    ):
        response = test_app_client.get(
            "/current-active-user",
            headers={"Authorization": f"Bearer {inactive_user.id}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_valid_token(self, test_app_client: TestClient, user: BaseUserDB):
        response = test_app_client.get(
            "/current-active-user", headers={"Authorization": f"Bearer {user.id}"}
        )
        assert response.status_code == status.HTTP_200_OK


class TestGetCurrentSuperuser:
    def test_missing_token(self, test_app_client: TestClient):
        response = test_app_client.get("/current-superuser")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token(self, test_app_client: TestClient):
        response = test_app_client.get(
            "/current-superuser", headers={"Authorization": "Bearer foo"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_valid_token_regular_user(
        self, test_app_client: TestClient, user: BaseUserDB
    ):
        response = test_app_client.get(
            "/current-superuser", headers={"Authorization": f"Bearer {user.id}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_valid_token_superuser(
        self, test_app_client: TestClient, superuser: BaseUserDB
    ):
        response = test_app_client.get(
            "/current-superuser", headers={"Authorization": f"Bearer {superuser.id}"}
        )
        assert response.status_code == status.HTTP_200_OK