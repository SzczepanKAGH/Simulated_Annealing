"""
Definition of two neighborhood functions ->

- The 'current_solution' parameter is in the form [Machine_object, Machine_object...]
- The returned solution is in the form [[path_1, path_2...], [] ...] - a route for one randomly selected machine
"""

import random

def neighbor_function_1(current_solution, search_depth, graph, T_max):
    """
    Function randomly selects a machine whose route will be modified.
    Then, by randomly selecting a path from the route, it tries to find a new route that avoids one vertex.
    Finally, it divides the entire route into the initial number of stages with the appropriate maximum time,
    resulting in a new route from a given vertex, which may be shorter/longer depending on the selected edges
    (limited by the maximum time and the number of stages).

    The most important parameter here is 'search_depth', which indicates how many vertices can be traversed
    to bypass a given vertex. If the parameter is large, due to the limitation of the number of stages and T_max,
    which may remove the obtained fragment of the solution, we can obtain a completely new route from the selected vertex.

    Best results for modifying the last stage; for others, there is a high probability of route repetition,
    especially with a large value of the 'search_depth' parameter.
    """

    # Randomly select one machine
    machine_id = random.randint(0, len(current_solution) - 1)
    machine = current_solution[machine_id]
    machine_speed = machine.speed
    machine_routes = [m.route for m in current_solution]
    initial_machine_routes = machine_routes
    route = machine.route

    # Solution in the form of [[]], where sublists are for different stages (for one machine)
    num_stages = len(route)  # Remember the number of stages
    # Combine sublists into one list
    route_list = [edge for sublist in route for edge in sublist]

    id1 = random.randint(0, len(route_list) - 2)  # Randomly select an edge
    id2 = id1 + 1

    stop_counter = 0  # Maximum traversal of subsequent paths - edge search
    if id1 == 0:
        stop_counter = len(route_list) - 2
    else:
        stop_counter = id1 - 1

    change = True
    route_change = True
    new_route = []  # New route bypassing one vertex

    while change:
        random_edge = route_list[id1]
        next_edge = route_list[id2]

        max_depth = search_depth
        start = random_edge.start
        goal = next_edge.end
        avoid = random_edge.end

        # Function that finds a new route bypassing a given vertex
        # max_depth - parameter that determines how deep the function can search for a new route
        # Returns a list of edges (new route) or an empty list ([]) if no route is found
        def find_new_route(start, goal, max_depth, avoid):
            visited = []  # List of visited vertices
            visited.append(avoid)  # Add the vertex to be avoided
            stack = [(start, 0, [])]  # Tuple (vertex, depth, list of edges)

            while stack:
                current_vertex, depth, path = stack.pop()

                if depth > max_depth:
                    continue
                if current_vertex == goal:
                    return path  # Return the list of edges forming the path
                if current_vertex in visited:
                    continue

                visited.append(current_vertex)

                # Add neighbors to the stack
                for neighbor in current_vertex.neighbors:
                    if neighbor not in visited:
                        # Find the edge connecting `current` and `neighbor`
                        edge = graph.get_edge(current_vertex, neighbor)
                        if edge:
                            # Create a new list of edges (path + edge)
                            new_path = path + [edge]
                            stack.append((neighbor, depth + 1, new_path))

            return []  # If no route is found, return an empty list

        new_route = find_new_route(start, goal, max_depth, avoid)

        # Move to the next path in the stage to find another bypass
        if new_route == []:
            if id1 == (len(route_list) - 2):
                id1 = 0
                id2 = 1

            else:
                id1 += 1
                id2 += 1
        else:
            change = False

        if id1 == stop_counter:
            route_change = False
            break

    if route_change:
        new_solution = route_list[0:id1] + new_route + route_list[id2+1:]

        # Now divide the entire list into the initial number of stages with the appropriate maximum time
        solution_list = [[] for _ in range(num_stages)]
        stage = 0
        time_cost = 0

        for edge in new_solution:
            edge_cost = edge.calculate_length() / machine_speed

            if time_cost + edge_cost > T_max:
                stage += 1
                time_cost = 0

                if stage > (num_stages - 1):
                    break
                else:
                    solution_list[stage].append(edge)
                    time_cost += edge_cost

            else:
                solution_list[stage].append(edge)
                time_cost += edge_cost

        if stage < len(solution_list):
            complete_stage(solution_list, stage, graph, T_max, machine_speed, param2=0)
        stage += 1

        while stage < num_stages:
            if stage < len(solution_list):
                complete_stage(solution_list, stage, graph, T_max, machine_speed, param2=0)
            stage += 1

        machine.route = solution_list
        machine_routes[machine_id] = solution_list

        return machine_routes

    else:
        print("No change!")
        return initial_machine_routes


def neighbor_function_2(current_solution, graph, T_max, param2=2):
    """
    Function randomly selects a machine whose route will be modified.
    Then, a random stage is selected (excluding the first one - from the base),
    where in the new solution, the previous stages are preserved, and the stages from the selected one
    are created entirely from scratch, selecting paths with higher priority
    (with some limitations on path looping).
    The newly created stages take into account the maximum time.

    The 'param2' parameter determines the number of remembered previous paths for the current
    path that cannot be repeated. The higher its value, the fewer repetitions, but the lower
    the priority weight.
    """

    # Randomly select one machine
    machine_id = random.randint(0, len(current_solution) - 1)
    machine = current_solution[machine_id]
    machine_speed = machine.speed
    machine_routes = [m.route for m in current_solution]
    route = machine.route

    # Solution in the form of [[]], where sublists are for different stages (for one machine)
    num_stages = len(route)  # Remember the number of stages
    if num_stages <= 1:
        return route
    stage = random.randint(1, num_stages - 1)  # Randomly select a stage (excluding the initial one)

    stages_to_modify = [idx for idx in range(1, num_stages) if len(route[idx]) > 0]
    if not stages_to_modify:
        print("No non-empty stage (except the first one) - no change!")
        return route

    stage = random.choice(stages_to_modify)

    new_solution = route[:stage]  # Preserve stages up to the selected one in unchanged form
    start = route[stage][0].start

    # Set of edges from the previous stage
    prev_stage = stage - 1
    visited_edges = set()
    for edge in route[prev_stage]:
        visited_edges.add(edge.start)
        visited_edges.add(edge.end)

    for stage_id in range(stage, num_stages):
        time_cost = 0
        new_route = []  # Route in the current stage

        while time_cost < T_max:
            # Sort neighbors of the vertex `start` by priority
            neighboring_edges = graph.get_edges_from_vertex(start)
            neighboring_edges.sort(key=lambda edge: -edge.priority)  # Sort descending by priority

            # Select the edge with the highest priority that does not lead to a visited vertex
            chosen_edge = None
            for edge in neighboring_edges:
                if edge.end not in [k.start for k in new_route[-param2:]] and edge.end not in visited_edges:
                    chosen_edge = edge
                    break
                elif edge.end not in [k.start for k in new_route[-param2:]]:
                    chosen_edge = edge
                    break

            if chosen_edge is None:
                if len(neighboring_edges) > 0:
                    chosen_edge = neighboring_edges[0]
                    # Fallback: take anything, even if it leads to a visited vertex.
                else:
                    break

            # Check if we exceed the maximum time
            if time_cost + chosen_edge.calculate_length() / machine_speed >= T_max:
                break

            else:
                # Add the chosen edge to the route and update the time
                new_route.append(chosen_edge)
                time_cost += chosen_edge.calculate_length() / machine_speed
                start = chosen_edge.end  # Update the current vertex

        if len(new_route) == 0:
            # If nothing was added in the entire while loop,
            # revert the modifications or try another method
            print("Stage turned out to be empty even with fallback - abandoning modification.")
            return route

        # Add the new route to the stage
        new_solution.append(new_route)

        visited_edges = set()
        for edge in route[stage_id]:
            visited_edges.add(edge.start)
            visited_edges.add(edge.end)

    if len(new_solution) > 0:  # Check if we have any stages
        if stage < len(new_solution):
            complete_stage(new_solution, stage_id, graph, T_max, machine_speed, param2=0)
        stage_id += 1

        while stage_id < num_stages:
            if stage < len(new_solution):
                complete_stage(new_solution, stage_id, graph, T_max, machine_speed, param2=0)
            stage_id += 1

    machine.route = new_solution
    machine_routes[machine_id] = new_solution

    return machine_routes


def complete_stage(solution_list, stage_index, graph, T_max, speed, param2=2):
    """
    Attempts to 'complete' the last stage (solution_list[stage_index]),
    if there is still time < T_max.
    Returns: nothing - directly modifies solution_list[stage_index].
    """

    # If there are no edges in this stage,
    # we need to determine the starting vertex:
    if len(solution_list[stage_index]) == 0:
        # Option A: take the end of the previous stage
        if stage_index == 0:
            # No previous stage, so no idea where to start.
            return
        else:
            # Take the last edge from the previous stage
            prev_stage = solution_list[stage_index - 1]
            if len(prev_stage) == 0:
                return  # Still no starting point
            start_vertex = prev_stage[-1].end
    else:
        # If there are edges, start from the end of the last one
        start_vertex = solution_list[stage_index][-1].end

    # Calculate the current time in the stage
    current_time = 0
    for edge in solution_list[stage_index]:
        current_time += edge.calculate_length() / speed

    # While there is time, try to add edges
    while True:
        if current_time >= T_max:
            break  # No time left

        # Find candidates (neighbors) from the graph
        neighbors = graph.get_edges_from_vertex(start_vertex)
        if not neighbors:
            break  # No further edges

        # Can sort by priority or take randomly:
        random.shuffle(neighbors)

        # Try to select an edge that still fits within T_max
        chosen_edge = None
        for edge in neighbors:
            if param2 > 0 and len(solution_list[stage_index]) > 0:
                recent_vertices = [k.end for k in solution_list[stage_index][-param2:]]
                if edge.end in recent_vertices:
                    continue

            cost = edge.calculate_length() / speed
            if current_time + cost <= T_max:
                chosen_edge = edge
                break

        if chosen_edge is None:
            # No suitable edge found
            break

        # Add the edge
        solution_list[stage_index].append(chosen_edge)
        current_time += chosen_edge.calculate_length() / speed
        start_vertex = chosen_edge.end