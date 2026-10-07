"""Search routines used by Hai's portion of Ex1_Maze.ipynb.

The functions do not modify the maze.  Each search returns a dictionary that
contains the solution path, action sequence, reached states, and metrics.
"""
from collections import deque
from time import perf_counter


_MOVES = (("N", (-1, 0)), ("E", (0, 1)), ("S", (1, 0)), ("W", (0, -1)))


class Node:
    """A search-tree node; compatible with the notebook's supplied Node class."""
    def __init__(self, pos, parent=None, action=None, cost=0):
        self.pos = tuple(pos)
        self.parent = parent
        self.action = action
        self.cost = cost

    def get_path_from_root(self):
        node, path = self, []
        while node is not None:
            path.append(node)
            node = node.parent
        return list(reversed(path))


def _goal_set(goal):
    """Accept one goal position or an iterable of goal positions."""
    if goal is None:
        return set()
    if (isinstance(goal, tuple) and len(goal) == 2
            and all(isinstance(value, (int, float)) for value in goal)):
        return {tuple(goal)}
    return {tuple(position) for position in goal}


def get_neighbors(maze, pos):
    """Yield legal (action, position) successors in N, E, S, W order."""
    rows, columns = maze.shape
    for action, (dr, dc) in _MOVES:
        next_pos = (pos[0] + dr, pos[1] + dc)
        if (0 <= next_pos[0] < rows and 0 <= next_pos[1] < columns
                and maze[next_pos[0], next_pos[1]] != "X"):
            yield action, next_pos


def _result(node, reached, expanded, max_depth, max_frontier,
            max_memory, started):
    path = None if node is None else node.get_path_from_root()
    return {
        "path": path,
        "actions": [] if path is None else [item.action for item in path[1:]],
        "reached": reached,
        "path_cost": None if node is None else node.cost,
        "nodes_expanded": expanded,
        "max_depth": max_depth,
        "max_frontier": max_frontier,
        "max_nodes_memory": max_memory,
        "time_seconds": perf_counter() - started,
    }


def bfs(maze, start, goal):
    """Breadth-first graph search; optimal when every move costs one."""
    started = perf_counter()
    goals = _goal_set(goal)
    root = Node(start, None, None, 0)
    frontier = deque([root])
    reached = {root.pos}
    expanded = max_depth = 0
    max_frontier = 1
    max_memory = 1

    while frontier:
        node = frontier.popleft()
        if node.pos in goals:
            return _result(node, reached, expanded, max_depth, max_frontier,
                           max_memory, started)
        expanded += 1
        for action, child_pos in get_neighbors(maze, node.pos):
            if child_pos not in reached:
                reached.add(child_pos)
                child = Node(child_pos, node, action, node.cost + 1)
                frontier.append(child)
                max_depth = max(max_depth, child.cost)
        max_frontier = max(max_frontier, len(frontier))
        max_memory = max(max_memory, len(frontier) + len(reached))
    return _result(None, reached, expanded, max_depth, max_frontier,
                   max_memory, started)


def dfs(maze, start, goal, max_expansions=50_000):
    """Memory-efficient DFS with path cycle checks and a safe expansion cap.

    The cap makes the difficult open-maze behavior observable without allowing a
    path-checking DFS to enumerate an impractical number of simple paths.
    """
    started = perf_counter()
    goals = _goal_set(goal)
    root = Node(start, None, None, 0)
    # A frame holds the current node and the index of its next successor.
    stack = [[root, 0, list(get_neighbors(maze, root.pos))]]
    active_path = {root.pos}
    seen_during_search = {root.pos}  # reporting only; never used for pruning
    expanded = max_depth = 0
    max_frontier = max_memory = 1

    while stack:
        node, child_index, successors = stack[-1]
        if child_index == 0:
            if node.pos in goals:
                return _result(node, seen_during_search, expanded, max_depth,
                               max_frontier, max_memory, started)
            if expanded >= max_expansions:
                return _result(None, seen_during_search, expanded, max_depth,
                               max_frontier, max_memory, started)
            expanded += 1
        if child_index == len(successors):
            active_path.remove(node.pos)
            stack.pop()                 # discard finished branch
            continue

        action, child_pos = successors[child_index]
        stack[-1][1] += 1
        if child_pos in active_path:    # prevents a cycle on this branch
            continue
        child = Node(child_pos, node, action, node.cost + 1)
        active_path.add(child_pos)
        seen_during_search.add(child_pos)
        stack.append([child, 0, list(get_neighbors(maze, child_pos))])
        max_depth = max(max_depth, child.cost)
        max_frontier = max(max_frontier, len(stack))
        max_memory = max(max_memory, len(stack))
    return _result(None, seen_during_search, expanded, max_depth,
                   max_frontier, max_memory, started)


def _depth_limited_dfs(maze, start, goals, limit):
    """One depth-limited, path-checking DFS pass used by IDS."""
    root = Node(start, None, None, 0)
    stack = [[root, 0, list(get_neighbors(maze, root.pos))]]
    active_path = {root.pos}
    seen = {root.pos}
    expanded = max_depth = 0
    max_frontier = max_memory = 1
    cutoff = False
    while stack:
        node, child_index, successors = stack[-1]
        if child_index == 0:
            if node.pos in goals:
                return node, seen, expanded, max_depth, max_frontier, max_memory, cutoff
            if node.cost == limit:
                cutoff = True
                active_path.remove(node.pos)
                stack.pop()
                continue
            expanded += 1
        if child_index == len(successors):
            active_path.remove(node.pos)
            stack.pop()
            continue
        action, child_pos = successors[child_index]
        stack[-1][1] += 1
        if child_pos in active_path:
            continue
        child = Node(child_pos, node, action, node.cost + 1)
        active_path.add(child_pos)
        seen.add(child_pos)
        stack.append([child, 0, list(get_neighbors(maze, child_pos))])
        max_depth = max(max_depth, child.cost)
        max_frontier = max(max_frontier, len(stack))
        max_memory = max(max_memory, len(stack))
    return None, seen, expanded, max_depth, max_frontier, max_memory, cutoff


def ids(maze, start, goal, max_depth=None):
    """Iterative deepening search, complete and optimal for unit step costs."""
    started = perf_counter()
    goals = _goal_set(goal)
    if max_depth is None:
        max_depth = maze.shape[0] * maze.shape[1] - 1
    total_expanded = max_seen_depth = peak_frontier = peak_memory = 0
    all_seen = set()
    for limit in range(max_depth + 1):
        node, seen, expanded, depth, frontier, memory, cutoff = _depth_limited_dfs(
            maze, start, goals, limit)
        all_seen.update(seen)
        total_expanded += expanded
        max_seen_depth = max(max_seen_depth, depth)
        peak_frontier = max(peak_frontier, frontier)
        peak_memory = max(peak_memory, memory)
        if node is not None:
            return _result(node, all_seen, total_expanded, max_seen_depth,
                           peak_frontier, peak_memory, started)
        if not cutoff:
            break
    return _result(None, all_seen, total_expanded, max_seen_depth,
                   peak_frontier, peak_memory, started)
