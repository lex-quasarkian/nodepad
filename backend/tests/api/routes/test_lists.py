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
    nodes = sorted(content["nodes"], key=lambda x: float(x["position"]))
    for i in range(len(data["nodes"])):
        assert nodes[i]["content"] in [n["content"] for n in data["nodes"]]
        assert float(nodes[i]["position"]) == (i + 1) * 1000.0
    assert "id" in content
    assert "owner_id" in content


def test_update_list_with_nodes_fractional_positioning(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # 1. Create a list with 2 nodes
    create_data = {
        "title": "Test List",
        "nodes": [{"content": "node1"}, {"content": "node3"}],
    }
    response = client.post(
        f"{settings.API_V1_STR}/lists/",
        headers=superuser_token_headers,
        json=create_data,
    )
    assert response.status_code == 200
    content = response.json()
    list_id = content["id"]
    nodes = content["nodes"]
    assert len(nodes) == 2
    assert float(nodes[0]["position"]) == 1000.0
    assert float(nodes[1]["position"]) == 2000.0

    # 2. Update list: Insert a node between node1 and node3, and add one at the end
    node1 = nodes[0]
    node3 = nodes[1]

    update_data = {
        "title": "Updated Test List",
        "nodes": [
            node1,
            {"content": "node2"},  # new node between 1 and 3
            node3,
            {"content": "node4"},  # new node at the end
        ],
    }

    update_response = client.put(
        f"{settings.API_V1_STR}/lists/{list_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert update_response.status_code == 200
    updated_content = update_response.json()
    updated_nodes = sorted(updated_content["nodes"], key=lambda x: float(x["position"]))
    assert len(updated_nodes) == 4

    # Check positions
    # node1 should still be 1000.0
    assert float(updated_nodes[0]["position"]) == 1000.0
    # new node2 should be exactly between 1000.0 and 2000.0 -> 1500.0
    assert float(updated_nodes[1]["position"]) == 1500.0
    assert updated_nodes[1]["content"] == "node2"
    # node3 should still be 2000.0
    assert float(updated_nodes[2]["position"]) == 2000.0
    # new node4 should be at the end, so node3.position + 1000.0 -> 3000.0
    assert float(updated_nodes[3]["position"]) == 3000.0
    assert updated_nodes[3]["content"] == "node4"

    # 3. Update list: Move node4 to the beginning
    node4 = updated_nodes[3]
    node2 = updated_nodes[1]

    reorder_data = {
        "title": "Reordered Test List",
        "nodes": [node4, node1, node2, node3],
    }

    reorder_response = client.put(
        f"{settings.API_V1_STR}/lists/{list_id}",
        headers=superuser_token_headers,
        json=reorder_data,
    )
    assert reorder_response.status_code == 200
    reordered_content = reorder_response.json()
    reordered_nodes = sorted(
        reordered_content["nodes"], key=lambda x: float(x["position"])
    )
    assert len(reordered_nodes) == 4

    # node4 was moved to start, so its new position should be node1.position - 1000 -> 0.0
    assert reordered_nodes[0]["id"] == node4["id"]
    assert float(reordered_nodes[0]["position"]) == 0.0
    # Other nodes should retain their positions
    assert reordered_nodes[1]["id"] == node1["id"]
    assert float(reordered_nodes[1]["position"]) == 1000.0
    assert reordered_nodes[2]["id"] == node2["id"]
    assert float(reordered_nodes[2]["position"]) == 1500.0


def test_create_list_with_many_nodes(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "title": "Many Nodes",
        "nodes": [{"content": f"node{i}"} for i in range(5)],
    }
    response = client.post(
        f"{settings.API_V1_STR}/lists/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    nodes = sorted(response.json()["nodes"], key=lambda x: float(x["position"]))
    assert len(nodes) == 5
    for i in range(5):
        assert float(nodes[i]["position"]) == (i + 1) * 1000.0


def test_create_list_with_single_node(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "title": "Single Node",
        "nodes": [{"content": "solo"}],
    }
    response = client.post(
        f"{settings.API_V1_STR}/lists/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    nodes = response.json()["nodes"]
    assert len(nodes) == 1
    assert float(nodes[0]["position"]) == 1000.0


def test_update_list_complex_reorder(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # Create 5 nodes
    create_data = {
        "title": "List 5",
        "nodes": [{"content": f"n{i}"} for i in range(5)],
    }
    res = client.post(
        f"{settings.API_V1_STR}/lists/",
        headers=superuser_token_headers,
        json=create_data,
    )
    list_id = res.json()["id"]
    nodes = res.json()["nodes"]

    # Reverse the order
    reversed_nodes = nodes[::-1]
    update_data = {"title": "List 5", "nodes": reversed_nodes}

    update_res = client.put(
        f"{settings.API_V1_STR}/lists/{list_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    updated_nodes = sorted(
        update_res.json()["nodes"], key=lambda x: float(x["position"])
    )
    assert len(updated_nodes) == 5

    # In reversed array [n4, n3, n2, n1, n0] (originally 5000, 4000, 3000, 2000, 1000)
    # LIS is [1000] (n0). So n4, n3, n2, n1 are repositioned before n0.
    # n4 gets 0.0, n3 gets 500.0, n2 gets 750.0, n1 gets 875.0, n0 keeps 1000.0.
    assert updated_nodes[0]["content"] == reversed_nodes[0]["content"]
    assert updated_nodes[1]["content"] == reversed_nodes[1]["content"]
    assert updated_nodes[2]["content"] == reversed_nodes[2]["content"]
    assert updated_nodes[3]["content"] == reversed_nodes[3]["content"]
    assert updated_nodes[4]["content"] == reversed_nodes[4]["content"]

    # Ensure strictly increasing
    for i in range(4):
        assert float(updated_nodes[i]["position"]) < float(
            updated_nodes[i + 1]["position"]
        )


def test_update_list_insert_multiple_nodes(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    create_data = {
        "title": "Insert Multiple",
        "nodes": [{"content": "start"}, {"content": "end"}],
    }
    res = client.post(
        f"{settings.API_V1_STR}/lists/",
        headers=superuser_token_headers,
        json=create_data,
    )
    list_id = res.json()["id"]
    nodes = res.json()["nodes"]

    # Insert before start, between start and end, and after end
    update_data = {
        "title": "Insert Multiple",
        "nodes": [
            {"content": "new_first"},
            nodes[0],
            {"content": "new_middle"},
            nodes[1],
            {"content": "new_last"},
        ],
    }

    update_res = client.put(
        f"{settings.API_V1_STR}/lists/{list_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    updated_nodes = sorted(
        update_res.json()["nodes"], key=lambda x: float(x["position"])
    )
    assert len(updated_nodes) == 5

    # Check positions
    assert updated_nodes[0]["content"] == "new_first"
    assert float(updated_nodes[0]["position"]) == 0.0

    assert any(
        n["id"] == nodes[0]["id"] and float(n["position"]) == 1000.0
        for n in updated_nodes
    )
    assert any(
        n["content"] == "new_middle" and float(n["position"]) == 1500.0
        for n in updated_nodes
    )
    assert any(
        n["id"] == nodes[1]["id"] and float(n["position"]) == 2000.0
        for n in updated_nodes
    )
    assert any(
        n["content"] == "new_last" and float(n["position"]) == 3000.0
        for n in updated_nodes
    )


def test_update_list_delete_only_keeps_positions(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    create_data = {
        "title": "Delete Only",
        "nodes": [{"content": "a"}, {"content": "b"}, {"content": "c"}],
    }
    res = client.post(
        f"{settings.API_V1_STR}/lists/",
        headers=superuser_token_headers,
        json=create_data,
    )
    list_id = res.json()["id"]
    nodes = res.json()["nodes"]

    assert float(nodes[0]["position"]) == 1000.0
    assert float(nodes[1]["position"]) == 2000.0
    assert float(nodes[2]["position"]) == 3000.0

    # Delete node "b" (index 1)
    update_data = {
        "title": "Delete Only",
        "nodes": [nodes[0], nodes[2]],
    }

    update_res = client.put(
        f"{settings.API_V1_STR}/lists/{list_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    updated_nodes = update_res.json()["nodes"]
    assert len(updated_nodes) == 2

    # Check positions remained unchanged
    assert updated_nodes[0]["id"] == nodes[0]["id"]
    assert float(updated_nodes[0]["position"]) == 1000.0

    assert updated_nodes[1]["id"] == nodes[2]["id"]
    assert float(updated_nodes[1]["position"]) == 3000.0


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
