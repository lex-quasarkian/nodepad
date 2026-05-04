import uuid

from sqlalchemy_utils import Ltree

from app.services.nodes import calculate_path_and_level


def test_calculate_path_and_level_root():
    node_id = uuid.uuid4()
    path, level = calculate_path_and_level(node_id)
    assert path == Ltree(node_id.hex)
    assert level == 0

def test_calculate_path_and_level_child():
    parent_id = uuid.uuid4()
    parent_path = Ltree(parent_id.hex)
    parent_level = 0

    node_id = uuid.uuid4()
    path, level = calculate_path_and_level(node_id, parent_path, parent_level)

    assert path == Ltree(f"{parent_id.hex}.{node_id.hex}")
    assert level == 1

def test_calculate_path_and_level_nested():
    p1_id = uuid.uuid4()
    p2_id = uuid.uuid4()
    parent_path = Ltree(f"{p1_id.hex}.{p2_id.hex}")
    parent_level = 1

    node_id = uuid.uuid4()
    path, level = calculate_path_and_level(node_id, parent_path, parent_level)

    assert path == Ltree(f"{p1_id.hex}.{p2_id.hex}.{node_id.hex}")
    assert level == 2
