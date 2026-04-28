import uuid
from decimal import Decimal

from edwh_uuid7 import uuid7
from sqlalchemy.orm import Session

from app import models
from app.crud.nodes import (
    get_position_between,
    get_position_end,
    get_position_start,
    reindex_nodes,
)
from app.schemas.lists import NodeListCreate, NodeListUpdate, NodeUpdate


def create_list(
    *, session: Session, list_in: NodeListCreate, owner_id: uuid.UUID
) -> models.NodeList:
    db_list = models.NodeList(
        **list_in.model_dump(exclude_unset=True, exclude={"nodes"}), owner_id=owner_id
    )
    session.add(db_list)

    if list_in.nodes:
        parent_positions = {}
        for node_in in list_in.nodes:
            if node_in:
                node_data = node_in.model_dump()

                # Ensure position is set if missing, incrementing by 1000 per parent
                if node_data.get("position") is None:
                    parent_id = node_data.get("parent_id")
                    current_pos = parent_positions.get(parent_id, 0)
                    new_pos = current_pos + 1000
                    node_data["position"] = new_pos
                    parent_positions[parent_id] = new_pos

                db_node = models.Node(**node_data)
                db_list.nodes.append(db_node)
                session.add(db_node)

    session.commit()
    session.refresh(db_list)

    return db_list


def _get_lis_nodes(
    group: list[NodeUpdate], existing_nodes: dict[uuid.UUID, models.Node]
) -> set[uuid.UUID]:
    arr = []
    for node_in in group:
        if node_in.id and node_in.id in existing_nodes:
            db_node = existing_nodes[node_in.id]
            if db_node.parent_id == node_in.parent_id:
                arr.append((node_in.id, float(db_node.position)))

    if not arr:
        return set()

    n = len(arr)
    dp = [1] * n
    parent = [-1] * n

    for i in range(1, n):
        for j in range(i):
            if arr[i][1] > arr[j][1]:
                if dp[j] + 1 > dp[i]:
                    dp[i] = dp[j] + 1
                    parent[i] = j

    max_len = 0
    max_idx = -1
    for i in range(n):
        if dp[i] >= max_len:
            max_len = dp[i]
            max_idx = i

    lis_ids = set()
    curr = max_idx
    while curr != -1:
        lis_ids.add(arr[curr][0])
        curr = parent[curr]

    return lis_ids


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
                        db_node.parent_id = parent_id
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
                        pos = get_position_between(session, prev_db_node.id, right_id)

                        # Reindex check
                        left_pos = prev_db_node.position
                        right_pos = existing_nodes[right_id].position
                        if (
                            right_pos - left_pos < Decimal("1e-15")
                        ):  # if we have no place to insert new node without rounding of position
                            reindex_nodes(session, db_list.id, parent_id)
                    elif prev_db_node:
                        pos = get_position_end(session, db_list.id, parent_id)
                    elif right_id:
                        pos = get_position_start(session, db_list.id, parent_id)
                    else:
                        pos = get_position_end(session, db_list.id, parent_id)

                    if is_new:
                        node_id = uuid7()
                        db_node = models.Node(
                            id=node_id,
                            nodelist_id=db_list.id,
                            parent_id=parent_id,
                            content=node_in.content,
                            position=pos,
                        )
                        db_list.nodes.append(db_node)
                        session.add(db_node)
                        # We must add this new node to existing_nodes so it can be referenced
                        # by subsequent right_id calculations if they were somehow in LIS
                        # (though new nodes are never in lis_ids, but it's safe to have it)
                        existing_nodes[node_id] = db_node
                    else:
                        db_node.position = pos

                if db_node:
                    prev_db_node = db_node

    session.commit()
    session.refresh(db_list)
    return db_list
