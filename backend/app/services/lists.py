import uuid
from decimal import Decimal

from edwh_uuid7 import uuid7
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy_utils import Ltree

from app import models
from app.crud import nodes as crud_nodes
from app.schemas.lists import NodeListCreate, NodeListUpdate, NodeUpdate


def _get_lis_nodes(
    group: list[NodeUpdate], existing_nodes: dict[uuid.UUID, models.Node]
) -> set[uuid.UUID]:
    """
    Get the longest increasing subsequence of nodes in the group.

    Args:
        group: List of node updates
        existing_nodes: Dictionary of existing nodes

    Returns:
        Set of node IDs in the longest increasing subsequence
    """
    arr = []
    for node_in in group:
        if node_in.id and node_in.id in existing_nodes:
            db_node = existing_nodes[node_in.id]
            if db_node.parent_id == node_in.parent_id:
                # Use Decimal directly for precision
                arr.append((node_in.id, db_node.position))

    if not arr:
        return set()

    n = len(arr)
    # tails_indices[i] stores the index in 'arr' of the smallest tail
    # of all increasing subsequences of length i+1.
    tails_indices = [0]
    # predecessors[i] stores the index of the element before arr[i] in the LIS
    predecessors = [-1] * n

    for i in range(1, n):
        # Case 1: arr[i] extends the largest tail
        if arr[i][1] > arr[tails_indices[-1]][1]:
            predecessors[i] = tails_indices[-1]
            tails_indices.append(i)
            continue

        # Case 2: Binary search for the smallest tail >= arr[i][1]
        low, high = 0, len(tails_indices) - 1
        while low <= high:
            mid = (low + high) // 2
            if arr[tails_indices[mid]][1] < arr[i][1]:
                low = mid + 1
            else:
                high = mid - 1

        tails_indices[low] = i
        if low > 0:
            predecessors[i] = tails_indices[low - 1]

    # Reconstruct the sequence by backtracking through predecessors
    lis_ids = set()
    curr = tails_indices[-1]
    while curr != -1:
        lis_ids.add(arr[curr][0])
        curr = predecessors[curr]

    return lis_ids


# TODO: Refactor this to keep DB operations in crud. Reduce complexity.
def create_list(
    *, session: Session, list_in: NodeListCreate, owner_id: uuid.UUID
) -> models.NodeList:
    """
    Create a new list with nodes.

    Args:
        session: Database session
        list_in: List data
        owner_id: Owner user ID

    Returns:
        Created ORM list
    """
    db_list = models.NodeList(
        **list_in.model_dump(exclude_unset=True, exclude={"nodes"}), owner_id=owner_id
    )
    session.add(db_list)

    if list_in.nodes:
        parent_positions = {}
        created_nodes = {}
        for node_in in list_in.nodes:
            if node_in:
                node_data = node_in.model_dump()
                node_id = node_data.get("id") or uuid7()
                node_data["id"] = node_id

                # Ensure position is set if missing, incrementing by 1000 per parent
                if node_data.get("position") is None:
                    parent_id = node_data.get("parent_id")
                    current_pos = parent_positions.get(parent_id, 0)
                    new_pos = current_pos + 1000
                    node_data["position"] = new_pos
                    parent_positions[parent_id] = new_pos

                # Calculate path and level
                parent_id = node_data.get("parent_id")
                if parent_id is None:
                    node_data["path"] = Ltree(node_id.hex)
                    node_data["level"] = 0
                else:
                    parent = created_nodes.get(parent_id)
                    if not parent:
                        parent = session.get(models.Node, parent_id)

                    if parent:
                        node_data["path"] = parent.path + node_id.hex
                        node_data["level"] = parent.level + 1
                    else:
                        node_data["path"] = Ltree(node_id.hex)
                        node_data["level"] = 0

                db_node = models.Node(**node_data)
                db_list.nodes.append(db_node)
                session.add(db_node)
                created_nodes[node_id] = db_node

    session.commit()
    session.refresh(db_list)

    return db_list


# TODO: Refactor this to keep DB operations in crud. Reduce complexity.
def update_list(
    *, session: Session, db_list: models.NodeList, list_in: NodeListUpdate
) -> models.NodeList:
    # Update simple fields
    update_dict = list_in.model_dump(exclude_unset=True, exclude={"nodes"})
    for key, value in update_dict.items():
        setattr(db_list, key, value)

    if list_in.nodes is not None:
        existing_nodes = {node.id: node for node in db_list.nodes}
        incoming_nodes_by_id = {
            node_in.id: node_in for node_in in list_in.nodes if node_in and node_in.id
        }

        # 1. Delete nodes that are missing in the incoming list
        for node_id, db_node in list(existing_nodes.items()):
            if node_id not in incoming_nodes_by_id:
                session.delete(db_node)
                db_list.nodes.remove(db_node)

        session.flush()

        # 2. Process nodes to handle content updates and repositioning
        nodes_by_parent = {}
        for node_in in list_in.nodes:
            if not node_in:
                continue
            parent_id = node_in.parent_id
            if parent_id not in nodes_by_parent:
                nodes_by_parent[parent_id] = []
            nodes_by_parent[parent_id].append(node_in)

        for parent_id, group in nodes_by_parent.items():
            lis_ids = _get_lis_nodes(group, existing_nodes)
            prev_db_node = None
            for i, node_in in enumerate(group):
                is_new = node_in.id is None
                db_node = None if is_new else existing_nodes.get(node_in.id)

                needs_reposition = False

                if is_new:
                    needs_reposition = True
                elif db_node:
                    db_node.content = node_in.content
                    if db_node.parent_id != parent_id:
                        old_path = str(db_node.path)
                        db_node.parent_id = parent_id

                        # Update path and level for the node itself
                        if parent_id is None:
                            db_node.path = Ltree(db_node.id.hex)
                            db_node.level = 0
                        else:
                            parent = session.get(models.Node, parent_id)
                            if parent:
                                db_node.path = parent.path + db_node.id.hex
                                db_node.level = parent.level + 1
                            else:
                                db_node.path = Ltree(db_node.id.hex)
                                db_node.level = 0

                        # Cascading update for descendants
                        new_path = str(db_node.path)
                        session.execute(
                            text("""
                            UPDATE node
                            SET
                                path = :new_path || subpath(path, nlevel(:old_path)),
                                level = nlevel(:new_path || subpath(path, nlevel(:old_path))) - 1
                            WHERE path <@ :old_path AND id != :node_id
                        """),
                            {
                                "new_path": new_path,
                                "old_path": old_path,
                                "node_id": db_node.id,
                            },
                        )
                        needs_reposition = True
                    else:
                        if db_node.id not in lis_ids:
                            needs_reposition = True

                if needs_reposition:
                    session.flush()  # ensure previous inserts/updates are visible to CTE

                    # Find right_id: next node in group that is in LIS
                    right_id = None
                    for next_node_in in group[i + 1 :]:
                        if next_node_in.id and next_node_in.id in lis_ids:
                            right_id = next_node_in.id
                            break

                    pos = None
                    if prev_db_node and right_id:
                        pos = crud_nodes.get_position_between(
                            session, prev_db_node.id, right_id
                        )

                        # Reindex check
                        left_pos = prev_db_node.position
                        right_pos = existing_nodes[right_id].position
                        if (
                            right_pos - left_pos < Decimal("1e-15")
                        ):  # if we have no place to insert new node without rounding of position
                            crud_nodes.reindex_nodes(session, db_list.id, parent_id)
                    elif prev_db_node:
                        pos = crud_nodes.get_position_end(
                            session, db_list.id, parent_id
                        )
                    elif right_id:
                        pos = crud_nodes.get_position_start(
                            session, db_list.id, parent_id
                        )
                    else:
                        pos = crud_nodes.get_position_end(
                            session, db_list.id, parent_id
                        )

                    if is_new:
                        node_id = uuid7()

                        # Calculate path and level for new node
                        if parent_id is None:
                            path = Ltree(node_id.hex)
                            level = 0
                        else:
                            parent = session.get(models.Node, parent_id)
                            if parent:
                                path = parent.path + node_id.hex
                                level = parent.level + 1
                            else:
                                path = Ltree(node_id.hex)
                                level = 0

                        db_node = models.Node(
                            id=node_id,
                            nodelist_id=db_list.id,
                            parent_id=parent_id,
                            content=node_in.content,
                            position=pos,
                            path=path,
                            level=level,
                        )
                        db_list.nodes.append(db_node)
                        session.add(db_node)
                        existing_nodes[node_id] = db_node
                    else:
                        if db_node:
                            db_node.position = pos

                if db_node:
                    prev_db_node = db_node

    session.commit()
    session.refresh(db_list)
    return db_list
