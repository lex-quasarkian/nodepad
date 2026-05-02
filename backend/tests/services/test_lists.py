import uuid
from decimal import Decimal
from unittest.mock import MagicMock

from app.schemas.lists import NodeUpdate
from app.services.lists import _get_lis_nodes


def test_get_lis_nodes():
    # Setup
    node_id_1 = uuid.uuid4()
    node_id_2 = uuid.uuid4()
    node_id_3 = uuid.uuid4()
    node_id_4 = uuid.uuid4()
    node_id_5 = uuid.uuid4()

    # Original positions: A=10, B=20, C=30, D=40, E=50
    # New order: D, A, C, E, B
    # LIS should be A, C, E ([10, 30, 50])

    group = [
        NodeUpdate(id=node_id_4, content="D", parent_id=None),
        NodeUpdate(id=node_id_1, content="A", parent_id=None),
        NodeUpdate(id=node_id_3, content="C", parent_id=None),
        NodeUpdate(id=node_id_5, content="E", parent_id=None),
        NodeUpdate(id=node_id_2, content="B", parent_id=None),
    ]

    existing_nodes = {
        node_id_1: MagicMock(id=node_id_1, position=Decimal("10.0"), parent_id=None),
        node_id_2: MagicMock(id=node_id_2, position=Decimal("20.0"), parent_id=None),
        node_id_3: MagicMock(id=node_id_3, position=Decimal("30.0"), parent_id=None),
        node_id_4: MagicMock(id=node_id_4, position=Decimal("40.0"), parent_id=None),
        node_id_5: MagicMock(id=node_id_5, position=Decimal("50.0"), parent_id=None),
    }

    lis_ids = _get_lis_nodes(group, existing_nodes)

    assert node_id_1 in lis_ids
    assert node_id_3 in lis_ids
    assert node_id_5 in lis_ids
    assert node_id_2 not in lis_ids
    assert node_id_4 not in lis_ids
    assert len(lis_ids) == 3


def test_get_lis_nodes_empty():
    assert _get_lis_nodes([], {}) == set()


def test_get_lis_nodes_single():
    node_id = uuid.uuid4()
    group = [NodeUpdate(id=node_id, content="A", parent_id=None)]
    existing_nodes = {
        node_id: MagicMock(id=node_id, position=Decimal("10.0"), parent_id=None)
    }
    assert _get_lis_nodes(group, existing_nodes) == {node_id}
