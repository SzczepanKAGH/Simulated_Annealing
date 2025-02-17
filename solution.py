import math
import data_structures
from typing import List, Union
from neighborhood_SK import *
from neighborhood_MK import *


class Machine:
    def __init__(self, speed=30):
        self.speed = speed  # In Km/h
        self.route = []

    def generate_initial_route(self, road_layout, Tmax, number_of_stages, consider_priority=False):
        """
        Generate an initial route for the machine considering time constraints and optionally road priorities.

        Args:
            road_layout: Graph representing the road network
            Tmax: Maximum time allowed per stage
            number_of_stages: Number of snowfall stages to plan for
            consider_priority: Whether to consider road priorities in route selection
        """
        self.route = []

        current_location = road_layout.baza
        previous_location = None

        for stage_no in range(number_of_stages):
            time_cost = 0
            stage_route = []

            while True:
                neighbors = current_location.neighbors
                if not neighbors:
                    break

                # Filter out the previous location if we have other options
                valid_neighbors = [n for n in neighbors if n != previous_location or len(neighbors) == 1]

                if not valid_neighbors:
                    break

                if consider_priority:
                    # Create list of (priority, neighbor, edge) tuples
                    priority_options = []
                    for neighbor in valid_neighbors:
                        edge = road_layout.get_edge(current_location, neighbor)
                        # Add small random factor to break ties
                        adjusted_priority = edge.priority + random.random() * 0.1
                        priority_options.append((adjusted_priority, neighbor, edge))

                    # Sort by priority in descending order and select the highest priority option
                    priority_options.sort(reverse=True)
                    next_location = priority_options[0][1]
                    selected_edge = priority_options[0][2]
                else:
                    next_location = random.choice(valid_neighbors)
                    selected_edge = road_layout.get_edge(current_location, next_location)

                # Calculate new time cost
                new_time_cost = time_cost + selected_edge.calculate_length() / self.speed

                # Check if adding this edge would exceed time limit
                if new_time_cost >= Tmax:
                    break

                # Add edge to route and update positions
                stage_route.append(selected_edge)
                time_cost = new_time_cost
                previous_location = current_location
                current_location = next_location

                # Safety check - if we're stuck at the base with no valid moves, break
                if current_location == road_layout.baza and len(stage_route) > 0:
                    break

            self.route.append(stage_route)


class RoadClearingProblem:
    def __init__(self,
                 snowfall_forecast: List[int],
                 road_layout: data_structures.Graph,
                 machines: List[Machine],
                 Tmax: Union[int, float]):

        self.snowfall_forecast = snowfall_forecast
        self.road_layout = road_layout
        self.machines = machines
        self.danger = float("inf")
        self.Tmax = Tmax  # In hours

        self.get_initial_path()

        solutions = [machine.route for machine in self.machines]

        for route in solutions:
            print(route, '\n')

    def get_initial_path(self):
        for machine in self.machines:
            machine.generate_initial_route(self.road_layout, self.Tmax, len(self.snowfall_forecast))

    def simulated_annealing(self, initial_temperature, cooling_rate, max_iterations, choose_neighbour_function=None):
        # Calculate initial danger based on the current - initial solution
        '''
        :param initial_temperature:
        :param cooling_rate:
        :param max_iterations:
        :return: best_solution, best_danger, diagnostics -> list containing 4 lists:
                 first list -> history of generated dangers
                 second list -> history of best dangers
                 third list -> temperature history
        '''

        current_danger = self.simulate_danger()
        best_danger = current_danger

        temperature = initial_temperature

        diagnostics = [[best_danger], [best_danger], [temperature]]

        actual_solution = copy.deepcopy(self.machines)  # current solution
        best_solution = copy.deepcopy(self.machines)

        if choose_neighbour_function is None or set(choose_neighbour_function) == {0, 1, 2, 3}:  # use all neighborhood functions simultaneously
            choose_neighbour_function = [4]

        for iteration in range(max_iterations):
            print("\n")
            print("-----ITERATION ", iteration, "-------")

            # Generate neighboring solution
            self.generate_neighbor(temperature, choose_neighbour_function)

            # Simulate new solution and calculate danger
            new_danger = self.simulate_danger()
            print("NEW DANGER -> ", new_danger)

            # Calculate danger difference
            delta_danger = new_danger - current_danger
            print("Danger difference: ", delta_danger)

            # Accept solution based on Boltzmann function
            if delta_danger < 0 or random.random() < math.exp(-delta_danger / temperature):
                actual_solution = copy.deepcopy(self.machines)
                current_danger = new_danger

                # Update best solution
                if new_danger < best_danger:
                    best_solution = copy.deepcopy(actual_solution)
                    best_danger = new_danger

            else:
                # Otherwise, revert to the current solution
                self.machines = actual_solution

                # Cool down temperature
            temperature *= cooling_rate

            diagnostics[0].append(new_danger)
            diagnostics[1].append(current_danger)
            diagnostics[2].append(temperature)

            # Termination condition
            if temperature < 1e-3:
                print("Termination due to low temperature!")
                break

            if best_danger == 0:
                print("Termination by zeroing the objective function")
                break

        self.machines = best_solution
        return best_solution, best_danger, diagnostics

    def simulate_danger(self):
        """
        Simulates the danger for the given solution by going through all snowfall stages.
        First, it assigns the appropriate snow level to the streets in the current stage and then calculates the danger level,
        returning the sum of all stages.
        The entire simulation works on a copy of the road layout, preserving its original state.
        :return: Total danger level.
        """
        graph_start = copy.deepcopy(self.road_layout)  # Work on a copy to preserve the original state
        total_danger = 0

        for stage in range(len(self.snowfall_forecast)):
            # List of cleared streets by all machines in the current stage
            cleared_streets = []
            for m in self.machines:
                for street in m.route[stage]:
                    if street not in cleared_streets:
                        cleared_streets.append(street)

            for street in graph_start.edges:
                if street in cleared_streets:  # Check if the street has been cleared
                    street.snow_level = 0  # Street has been cleared
                else:
                    street.snow_level += self.snowfall_forecast[
                        stage]  # Add snow to streets that haven't been cleared

            # Calculate danger level for the current stage
            stage_level = sum(street.get_danger_level() for street in graph_start.edges)
            total_danger += stage_level

        return total_danger

    def generate_neighbor(self, actual_temperature, choose_neighbour_function):
        """
        Generates a new solution by using specific neighborhood functions.
        """
        graph_complexity = len(self.road_layout.edges)  # Number of edges/roads in the graph - describes complexity

        # Parameters for neighborhood function MK - adjusted to graph complexity
        search_depth = 6
        param2 = 4

        if graph_complexity > 200:
            search_depth = 12
            param2 = 8

        actual_temp = actual_temperature  # Temperature value in the current iteration

        # Selected neighborhood functions for the algorithm (parameter - choose_neighbour_function - default is choose_neighbour_function=[4] - use all functions)
        f_using = choose_neighbour_function

        # Selecting one of the options (specific neighborhood function or all)
        if len(f_using) == 1:

            # Option - all neighborhood functions - BEST OPTION - most comprehensive
            if f_using[0] == 4:
                # --- Stage I ---
                '''
                In the initial iterations, our solution can change more radically.
                '''
                if actual_temp > 1:
                    param_choose = random.randint(0, 100)  # Randomly select a parameter value

                    if param_choose < 65:
                        # Introduce more radical changes
                        search_depth = int(search_depth * 1.5)  # Increases potential route diversity in neighborhood function 0
                        choose_f = random.choice([0, 2, 3])

                    else:
                        search_depth = search_depth * 0.5  # Reduces route diversity in neighborhood function 0
                        param2 = int(param2 * 1.5)
                        choose_f = random.choice([0, 1])

                # --- Stage II ---
                '''
                In the next stage, we will randomly select a neighborhood function.
                '''
                if 0.01 < actual_temp <= 1:
                    search_depth = random.randint(int(search_depth * 0.5), int(search_depth * 2))
                    param2 = random.randint(int(param2 * 0.5), int(param2 * 2))
                    choose_f = random.choice([0, 1, 2, 3])

                # --- Stage III ---
                '''
                In the final stage, we will try to refine/improve our solution using less radical changes.
                '''
                if actual_temp <= 0.01:
                    param_choose = random.randint(0, 100)  # Randomly select a parameter value

                    if param_choose < 65:
                        # Introduce less radical changes
                        search_depth = int(search_depth * 0.5)  # Reduces route diversity in neighborhood function 0
                        param2 = int(param2 * 1.5)
                        choose_f = random.choice([0, 1])

                    else:
                        search_depth = int(search_depth * 1.5)  # Increases potential route diversity in neighborhood function 0
                        choose_f = random.choice([0, 2, 3])

            elif f_using[0] in [0, 1, 2, 3]:
                choose_f = f_using[0]

            else:
                print(
                    '''No neighborhood function provided!
                    Available:
                    0, 1, 2, 3 -> specific neighborhood functions
                    4 -> use all neighborhood functions simultaneously

                    Input format:
                    For single choice -> e.g., [2]
                    For multiple choices -> e.g., [0, 2]
                    '''
                )

        else:
            f_codes = [0, 1, 2, 3]
            if all(elem in f_codes for elem in f_using):
                choose_f = random.choice(f_using)

            else:
                print(
                    '''No neighborhood function provided!
                    Available:
                    0, 1, 2, 3 -> specific neighborhood functions
                    4 -> use all neighborhood functions simultaneously

                    Input format:
                    For single choice -> e.g., [2]
                    For multiple choices -> e.g., [0, 2]
                    '''
                )
        print(choose_f)
        # --- Used neighborhood functions ---

        if choose_f == 0:  # modify_route_avoiding_vertex
            neighbor_function_1(self.machines, search_depth, self.road_layout, self.Tmax)
            '''
            Modifies the existing route of a machine by avoiding one vertex, depending on the 'search_depth' parameter
            (the higher the parameter, the more diverse the new solution).
            '''

        elif choose_f == 1:  # reconstruct_route_from_stage
            neighbor_function_2(self.machines, self.road_layout, self.Tmax, param2)
            '''
            Reconstructs the route from a randomly selected stage, with the possibility of significant changes if early stages are selected.
            '''

        elif choose_f == 2:
            generate_route_from_least_frequent(self.machines, self.road_layout, self.Tmax)
            '''
            Generates a route from the base to the least frequented street and optionally adds streets to fill the time.
            Possibility of introducing larger changes.
            '''

        elif choose_f == 3:
            change_path(self.machines, self.road_layout, self.Tmax)
            '''
            Modifies the machine's route by removing one edge and replacing it with a new route repaired by the A* algorithm.
            Moves edges to the next stage if Tmax is exceeded.
            '''
