from edwh_uuid7 import uuid7
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from tests.utils.list import create_random_list


def test_create_list_without_nodes(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/lists/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content


def test_create_list_with_nodes(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "title": "Foo",
        "description": "Fighters",
        "nodes": [{"content": "bar"}, {"content": "baz"}],
    }
    response = client.post(
        f"{settings.API_V1_STR}/lists/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert len(content["nodes"]) == len(data["nodes"])
    for i in range(len(data["nodes"])):
        assert content["nodes"][i]["content"] == data["nodes"][i]["content"]
    assert "id" in content
    assert "owner_id" in content


def test_read_list(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    list = create_random_list(db)
    response = client.get(
        f"{settings.API_V1_STR}/lists/{list.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == list.title
    assert content["description"] == list.description
    assert content["id"] == str(list.id)
    assert content["owner_id"] == str(list.owner_id)


def test_read_list_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/lists/{uuid7()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "List not found"


def test_read_list_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    list = create_random_list(db)
    response = client.get(
        f"{settings.API_V1_STR}/lists/{list.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_read_lists(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_list(db)
    create_random_list(db)
    response = client.get(
        f"{settings.API_V1_STR}/lists/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


def test_update_list(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    list = create_random_list(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/lists/{list.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] == str(list.id)
    assert content["owner_id"] == str(list.owner_id)


def test_update_list_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/lists/{uuid7()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "List not found"


def test_update_list_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    list = create_random_list(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/lists/{list.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_delete_list(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    list = create_random_list(db)
    response = client.delete(
        f"{settings.API_V1_STR}/lists/{list.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "List deleted successfully"


def test_delete_list_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/lists/{uuid7()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "List not found"


def test_delete_list_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    list = create_random_list(db)
    response = client.delete(
        f"{settings.API_V1_STR}/lists/{list.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"
