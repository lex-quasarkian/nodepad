import uuid
from collections import defaultdict
from decimal import Decimal
from itertools import count

from sqlalchemy.orm import Session

from app import models, services
from app.crud import nodes as crud_nodes
from app.schemas.lists import NodeListCreate, NodeListUpdate


def get_list(session: Session, *, id: uuid.UUID) -> models.NodeList | None:
    return session.get(models.NodeList, id)


def create_list(
    *, session: Session, list_in: NodeListCreate, owner_id: uuid.UUID
) -> models.NodeList:
    from edwh_uuid7 import uuid7

    db_list = models.NodeList(
        **list_in.model_dump(exclude_unset=True, exclude={"nodes"}), owner_id=owner_id
    )
    session.add(db_list)

    if list_in.nodes:
        # Use a counter that starts at 1000 and increments by 1000 for each parent
        parent_counters = defaultdict(lambda: count(1000, 1000))
        created_nodes = {}
        for node_in in list_in.nodes:
            if node_in:
                node_data = node_in.model_dump()
                node_id = node_data.get("id") or uuid7()
                node_data["id"] = node_id

                # Ensure position is set if missing
                if node_data.get("position") is None:
                    node_data["position"] = next(parent_counters[node_data.get("parent_id")])
                else:
                    # Update the counter for this parent if a position was provided
                    # to avoid collisions if subsequent nodes have no position.
                    # Note: this is a simple heuristic.
                    pos = int(node_data["position"])
                    parent_counters[node_data.get("parent_id")] = count(pos + 1000, 1000)

                # Calculate path and level
                parent_id = node_data.get("parent_id")
                parent = created_nodes.get(parent_id)
                if not parent and parent_id:
                    parent = session.get(models.Node, parent_id)

                path, level = services.nodes.calculate_path_and_level(
                    node_id,
                    parent.path if parent else None,
                    parent.level if parent else None,
                )
                node_data["path"] = path
                node_data["level"] = level

                db_node = models.Node(**node_data)
                db_list.nodes.append(db_node)
                session.add(db_node)
                created_nodes[node_id] = db_node

    session.commit()
    session.refresh(db_list)

    return db_list


def update_list(
    *, session: Session, db_list: models.NodeList, list_in: NodeListUpdate
) -> models.NodeList:
    from edwh_uuid7 import uuid7

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
        nodes_by_parent = defaultdict(list)
        for node_in in list_in.nodes:
            if node_in:
                nodes_by_parent[node_in.parent_id].append(node_in)

        for parent_id, group in nodes_by_parent.items():
            lis_ids = services.lists.get_lis_nodes(group, existing_nodes)
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
                        parent = (
                            session.get(models.Node, parent_id) if parent_id else None
                        )
                        new_path, new_level = services.nodes.calculate_path_and_level(
                            db_node.id,
                            parent.path if parent else None,
                            parent.level if parent else None,
                        )
                        db_node.path = new_path
                        db_node.level = new_level

                        # Cascading update for descendants
                        crud_nodes.apply_cascading_path_update(
                            session,
                            node_id=db_node.id,
                            old_path=old_path,
                            new_path=str(new_path),
                        )
                        needs_reposition = True
                    else:
                        if db_node.id not in lis_ids:
                            needs_reposition = True

                if needs_reposition:
                    session.flush()  # ensure previous inserts/updates are visible

                    # Find right_id: next node in group that is in LIS
                    right_id = next(
                        (
                            next_node_in.id
                            for next_node_in in group[i + 1 :]
                            if next_node_in.id and next_node_in.id in lis_ids
                        ),
                        None,
                    )

                    pos = None
                    if prev_db_node and right_id:
                        pos = crud_nodes.get_position_between(
                            session, prev_db_node.id, right_id
                        )

                        # Reindex check
                        left_pos = prev_db_node.position
                        right_pos = existing_nodes[right_id].position
                        if right_pos - left_pos < Decimal(
                            "1e-15"
                        ):  # if we have no place to insert
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

                        parent = (
                            session.get(models.Node, parent_id) if parent_id else None
                        )
                        path, level = services.nodes.calculate_path_and_level(
                            node_id,
                            parent.path if parent else None,
                            parent.level if parent else None,
                        )

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
