import uuid

from sqlalchemy_utils import Ltree


def calculate_path_and_level(
    node_id: uuid.UUID,
    parent_path: Ltree | None = None,
    parent_level: int | None = None
) -> tuple[Ltree, int]:
    """
    Calculate path and level for a node based on its parent.
    This is a pure logic function with no DB access.
    """
    if parent_path is None:
        return Ltree(node_id.hex), 0

    # Use Ltree concatenation. parent_path + node_id.hex works in sqlalchemy_utils.
    # But for safety and consistency with previous code, we can use the string format if needed.
    # The previous code used: parent.path + db_node.id.hex
    return parent_path + node_id.hex, (parent_level if parent_level is not None else 0) + 1
