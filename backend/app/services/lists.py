import bisect
import uuid
from typing import Any

from app import models
from app.schemas.lists import NodeUpdate


def _reconstruct_lis(
    arr: list[tuple[uuid.UUID, Any]], tail_indices: list[int], predecessors: list[int]
) -> set[uuid.UUID]:
    """
    Reconstruct the LIS IDs by backtracking through predecessors.
    """
    lis_ids = set()
    if not tail_indices:
        return lis_ids

    curr = tail_indices[-1]
    while curr != -1:
        lis_ids.add(arr[curr][0])
        curr = predecessors[curr]
    return lis_ids


def _prepare_lis_input(
    group: list[NodeUpdate], existing_nodes: dict[uuid.UUID, models.Node]
) -> list[tuple[uuid.UUID, Any]]:
    """
    Filter incoming nodes: keep only those already in the DB
    and belonging to the same parent. Returns a list of (id, position).
    """
    return [
        (node_in.id, existing_nodes[node_in.id].position)
        for node_in in group
        if node_in.id
        and node_in.id in existing_nodes
        and existing_nodes[node_in.id].parent_id == node_in.parent_id
    ]


def _calculate_lis_indices(
    arr: list[tuple[uuid.UUID, Any]],
) -> tuple[list[int], list[int]]:
    """
    Calculate tail indices and predecessors for the Longest Increasing Subsequence.
    Uses the patience sorting algorithm with binary search (bisect).
    """
    # tails: stores the smallest tail values for each possible LIS length.
    # tail_indices: stores the corresponding indices in the original 'arr'.
    # predecessors: stores the index of the previous element in the subsequence.
    tails = []
    tail_indices = []
    predecessors = [-1] * len(arr)

    for i, (_, pos) in enumerate(arr):
        # find the insertion point for 'pos' in the sorted 'tails' list.
        # bisect_left provides O(log N) search.
        idx = bisect.bisect_left(tails, pos)

        if idx < len(tails):
            # Found an existing subsequence that can be ended with a smaller value (optimized).
            tails[idx] = pos
            tail_indices[idx] = i
        else:
            # 'pos' is larger than all current tails, it extends the LIS.
            tails.append(pos)
            tail_indices.append(i)

        if idx > 0:
            # Link to the tail of the subsequence with length (idx - 1).
            predecessors[i] = tail_indices[idx - 1]

    return tail_indices, predecessors


def get_lis_nodes(
    group: list[NodeUpdate], existing_nodes: dict[uuid.UUID, models.Node]
) -> set[uuid.UUID]:
    """
    Main function to get the set of node IDs that should not be moved.
    Complexity is O(N log N).
    """
    arr = _prepare_lis_input(group, existing_nodes)
    if not arr:
        return set()

    tail_indices, predecessors = _calculate_lis_indices(arr)
    return _reconstruct_lis(arr, tail_indices, predecessors)
