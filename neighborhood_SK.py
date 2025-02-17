import heapq
import random
import copy


def find_path_to_edge(road_layout, target_edge, machine_speed):
    """
    Find path from base to the start of target edge using A* algorithm.
    Returns path and total time cost.
    """
    open_set = [(0, road_layout.baza, [])]
    closed_set = set()

    # Target nodes are both start and end of the target edge

    while open_set:
        f_score, current, path = heapq.heappop(open_set)

        if current == target_edge.start:
            total_time = sum(edge.calculate_length() for edge in path) / machine_speed
            return path, total_time, current

        if current in closed_set:
            continue

        closed_set.add(current)

        for neighbor in current.neighbors:
            if neighbor in closed_set:
                continue

            edge = road_layout.get_edge(current, neighbor)

            new_path = path + [edge]
            g_score = sum(e.calculate_length() for e in new_path)
            # Use minimum distance to either end of target edge as heuristic
            h_score = neighbor.get_distance(target_edge.start) # road_layout.get_edge(neighbor, target_edge.start).dlugosc
            f_score = g_score + h_score

            heapq.heappush(open_set, (f_score, neighbor, new_path))

    return None, 0, None


def fill_remaining_time(road_layout, start_node, remaining_time, machine_speed):
    """
    Fill remaining time with additional edges using a greedy approach.
    """
    additional_route = []
    last_node = None
    current_node = start_node
    time_used = 0
    # print(remaining_time)

    while True:
        # Get valid neighbors (excluding those that would create a dead end)
        valid_neighbors = [n for n in current_node.neighbors
                           if (len(n.neighbors) > 1 or n == road_layout.baza) and n != last_node]

        if not valid_neighbors:
            # Case when only valid neighbor is the one from which we came from
            valid_neighbors = [last_node]

        # Choose next edge
        next_node = random.choice(valid_neighbors)
            
        edge = road_layout.get_edge(current_node, next_node)

        # Check if adding this edge would exceed remaining time
        time_cost = edge.calculate_length() / machine_speed
        if time_used + time_cost > remaining_time:
            break

        additional_route.append(edge)
        time_used += time_cost

        # We save last node in order to prohibit backtracking
        last_node = current_node
        current_node = next_node

    return additional_route, time_used


def generate_route_from_least_frequent(machines, road_layout, Tmax, consider_priority=False):
    """
    Generuje trasęz bazy do najmniej uczęszczanej ulicy i
    ewentualnie dokłada ulice na koniec trasy, aby wypełnić czas.
    """

    current_machine = random.choice(machines)
    num_of_stages = len(current_machine.route)

    def calculate_street_frequency(edge):
        frequency = 0
        for machine in machines:
            if machine != current_machine:  # Don't count current machine
                for stage_index in range(num_of_stages):
                    frequency += sum(1 for route_edge in machine.route[stage_index]
                                     if route_edge == edge)

        # If considering priority, adjust frequency score by priority
        if consider_priority:
            # Normalize frequency to 0-1 range and combine with priority
            # Lower frequency and higher priority will give lower score
            freq_score = frequency / (len(machines) - 1) if len(machines) > 1 else 1
            priority_score = 1 - (edge.priority / max(e.priority for e in road_layout.edges))
            return (freq_score + priority_score) / 2
        return frequency

    # Calculate frequencies for all edges
    edge_scores = [(calculate_street_frequency(edge), edge) for edge in road_layout.edges]
    edge_scores.sort(key=lambda x: x[0])  # Sort by frequency/score

    # Try edges starting from least frequent
    for _, target_edge in edge_scores:
        # Find path from base to target edge
        path_to_edge, time_to_edge, reached_node = find_path_to_edge(
            road_layout,
            target_edge,
            current_machine.speed
        )

        # print(current_machine.route)
        if path_to_edge is not None:
            # Add the target edge to the path
            route = path_to_edge + [target_edge]

            # Calculate time cost of path for all stages including initial edge
            time_cost = (sum(edge.calculate_length() for edge in route) / current_machine.speed)

            if time_cost <= Tmax * num_of_stages:
                # Try to fill remaining time
                remaining_time = Tmax * num_of_stages - time_cost
                if remaining_time > 0:
                    additional_edges, additional_time = fill_remaining_time(
                        road_layout,
                        route[-1].end,
                        remaining_time,
                        current_machine.speed
                    )

                    route.extend(additional_edges)

                # print(route)
                route = [route] + [[] for _ in range(num_of_stages - 1)]
                route = adjust_route_to_tmax(route, current_machine, Tmax)
                # print(route)
                current_machine.route = route
                return route

    # If no valid route found, return empty route
    return []


def adjust_route_to_tmax(new_route, machine, Tmax):
    """
    Dostosowuje trasę do maksymalnego czasu Tmax, przesuwając nadmiarowe krawędzie
    do następnego segmentu lub usuwając je, jeśli to ostatni segment.
    """

    for segment_idx in range(len(new_route)):
        while True:
            time = 0
            edges_to_move = []

            # Oblicz całkowity czas dla bieżącego segmentu
            for edge_idx, edge in enumerate(new_route[segment_idx]):
                time += edge.length / machine.speed

                # Jeśli czas przekracza Tmax, przygotuj się do przesunięcia krawędzi
                if time > Tmax:
                    edges_to_move.append((edge_idx, edge))

            # Jeśli nie ma krawędzi do przesunięcia, zakończ pętlę
            if not edges_to_move:
                break

            # Przesuń nadmiarowe krawędzie do kolejnego segmentu
            if segment_idx < len(new_route) - 1:
                for edge_idx, edge in reversed(edges_to_move):
                    # Krawędź pod danym indeksem ustawiamy na None, aby uniknąć usunięcia z segmentu trasy
                    # wszystkich wystąpień danej krawędzi
                    new_route[segment_idx][edge_idx] = None
                    new_route[segment_idx + 1].insert(0, edge)

            else:
                # Jeśli to ostatni segment, usuń nadmiarowe krawędzie
                for edge_idx, edge in edges_to_move:
                    new_route[segment_idx][edge_idx] = None

            # Usuwanie z segmentu wszystkich None'ów
            new_route[segment_idx] = [edge for edge in new_route[segment_idx] if edge is not None]

    return new_route


def change_path(machines, road_layout, Tmax):
    """
        Modyfikuje trasę maszyny, usuwając jedną krawędź i zastępując ją nową trasą naprawioną algorytmem A*.
        Przenosi krawędzie do następnego etapu, jeśli Tmax zostanie przekroczone.

        Args:
            machines (List[Machine]): Lista maszyn.
            road_layout (Graph): Graf reprezentujący układ drogowy.
            Tmax (float): Maksymalny czas na segment trasy.

        Returns:
            list: Zaktualizowane trasy dla maszyn.
        """

    def repair_path_A_star(removed_edge, graph):
        open_set = []
        heapq.heappush(open_set, (0, removed_edge.start))  # Kolejka priorytetowa
        closed_set = set()  # Zbiór odwiedzonych węzłów
        came_from = {}  # Przechowuje ścieżkę (z wierzchołka na wierzchołek)
        g_score = {node: float('inf') for node in graph.vertices}  # Koszt dotarcia
        g_score[removed_edge.start] = 0

        while open_set:
            _, current = heapq.heappop(open_set)

            # Jeśli dotarliśmy do celu, rekonstruujemy ścieżkę
            if current == removed_edge.end:
                path = []
                while current in came_from:
                    prev_node = came_from[current]
                    edge = graph.get_edge(prev_node, current)
                    path.append(edge)
                    current = prev_node
                return path[::-1]  # Odwróć kolejność, by zaczynać od startu

            # Dodaj węzeł do zbioru odwiedzonych
            closed_set.add(current)

            # Iterujemy po sąsiadach wierzchołka
            for neighbor in current.neighbors:
                edge = graph.get_edge(current, neighbor)

                # Ignorujemy krawędź usuniętą
                if edge == removed_edge:
                    continue

                # Ignorujemy węzły już odwiedzone
                if neighbor in closed_set:
                    continue

                # Oblicz koszt przejścia
                tentative_g_score = g_score[current] + current.get_distance(neighbor)
                # graph.get_edge(current, neighbor).dlugosc

                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current  # Zaktualizuj ścieżkę
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + neighbor.get_distance(removed_edge.end)
                    # graph.get_edge(neighbor, removed_edge.koniec).dlugosc # Heurystyka (odległość do celu)
                    heapq.heappush(open_set, (f_score, neighbor))

            # print('dasdas')
        return None  # Jeśli nie znaleziono ścieżki

    machine = random.choice(machines)
    machine_copy = copy.deepcopy(machine)
    new_route = machine_copy.route

    segment_idx = random.choice(range(len(new_route)))

    # if len(new_route[segment_idx]) == 0:
    #     return None
    #
    try:
        edge_for_deletion_idx = random.choice(range(len(new_route[segment_idx])))

    except IndexError:
        print(new_route[segment_idx])

    edge_for_deletion = new_route[segment_idx][edge_for_deletion_idx]

    repaired_path = repair_path_A_star(edge_for_deletion, road_layout)
    # print(repaired_path)

    if repaired_path is not None:
        # Replace the deleted edge with the repaired path
        new_route[segment_idx][edge_for_deletion_idx:edge_for_deletion_idx + 1] = repaired_path
        new_route = adjust_route_to_tmax(new_route, machine, Tmax)
        # print(new_route)

    machine.route = new_route

    return [machine.route for machine in machines]


# ---------- JESZCZE NIE DZIAŁA -------------- #
def squish_routes(machines, road_layout, Tmax):
    """
    Stara się zoptymalizować trasy poprzez ściśnięcie tras dla każdej maszyny. Najpierw, jeżeli to możliwe przesuwa
    krawędzie do poprzedniego etapu, aby na koniec uzupełnić ostatni etap najkrótszą krawędzią sąsiadującą, która nie
    jest odśnieżona.

    :param machines:
    :param road_layout:
    :param Tmax:
    :return:
    """

    for machine in machines:
        route = machine.route
        for stage_idx in range(1, len(machine.route) - 1):
            stage_time = 0
            for edge in route[stage_idx]:
                stage_time += edge.length / machine.speed

            next_stage_first_edge = route[stage_idx + 1][0]

            if stage_time + next_stage_first_edge.length / machine.speed < Tmax:
                route[stage_idx].append(route[stage_idx + 1].pop(0))
                print('lista ściśnięta')

        # Próbujemy dodać dodatkowe krawędzie do ostatniego etapu
        last_stage_time = 0
        last_node = [edge for stage in route for edge in stage][-1].end
        for edge in route[-1]:
            last_stage_time += edge.length / machine.speed

        possible_edges = []
        for neighbor in last_node.neighbors:
            possible_edges.append(road_layout.get_edge(last_node, neighbor))

        possible_edges.sort(key=lambda x: x.length)
        possible_edges = [edge for edge in possible_edges if edge.snow_level != 0]

        while possible_edges:
            shortest_edge = possible_edges.pop(0)
            last_stage_time += shortest_edge.length / machine.speed

            if last_stage_time > Tmax:
                break

            machine.route[-1].append(shortest_edge)
            print('dodano element')

    return [machine.route for machine in machines]
