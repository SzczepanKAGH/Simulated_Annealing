# Simulated Annealing for Snowplow Route Optimization in Urban Environments

This repository contains a project developed by me and two other students during the second operations research course. The goal is to optimize the deployment of snowplows to clear city streets as quickly and efficiently as possible.


## Introduction
The problem involves planning the deployment of snowplows to clear streets in a city, taking into account factors such as road priority, machine capacity, and worker availability. Simulated annealing was chosen as the optimization technique due to its ability to handle complex, non-linear problems.



## What is Subject to Optimization
The main objective is to optimize the distribution of machine workloads to minimize the time required to clear all streets. This is a single-criterion optimization problem focused on time efficiency.



## How Does It Work
The algorithm is managed through a graphical interface built with `tkinter`. Users can configure variables such as city layout, snowfall prediction, and machine parameters. The simulated annealing algorithm then optimizes the routes based on these inputs.



## Key Features

### 1. **City Layout**
The city layout is represented as a graph, where:
- **Vertices** represent street intersections.
- **Edges** represent roads connecting these intersections.

The layout can be configured in two ways:
- **Pre-configured layouts**: Generated using the `OSMnx` library, which allows for the creation of realistic city road networks based on OpenStreetMap data.
- **Custom layouts**: Loaded from a `.txt` file, where the user can define their own graph structure. This is useful for testing specific scenarios or smaller, custom road networks.


### 2. **Snowfall Prediction**
Snowfall is modeled as a list of numerical values, where each value represents the amount of snow that falls during a specific stage. For example:
- `[10, 5, 15]` means 10 units of snow fall in the first stage, 5 units in the second stage, and 15 units in the third stage.

This feature allows the algorithm to simulate real-world conditions where snowfall varies over time. The stages are separated by a user-defined time interval, which can be adjusted to reflect different snowfall patterns (e.g., light snow over several hours or heavy snow in a short period).



### 3. **Machines (Snowplows)**
The system supports the configuration of up to six snowplows, each with given speed at which the snowplow can clear snow. This affects how much ground a machine can cover in a given time.


### 4. **Simulated Annealing Parameters**
The simulated annealing algorithm is controlled by several key parameters:
- **Temperature**: Controls the probability of accepting worse solutions during the search.
  - **High temperature**: Allows the algorithm to explore a wider range of solutions, even if they are suboptimal.
  - **Low temperature**: Focuses on refining and improving the current solution.
- **Cooling Rate**: Determines how quickly the temperature decreases over time.
  - A slower cooling rate allows for more thorough exploration of the solution space.
  - A faster cooling rate may lead to quicker convergence but risks getting stuck in local optima.
- **Number of Iterations**: Defines the total number of iterations the algorithm will perform.
  - For complex graphs (e.g., those generated with `OSMnx`), it is recommended to keep the number of iterations around 200 to balance performance and solution quality.
  - For simpler graphs (e.g., those loaded from `.txt` files), a higher number of iterations such as 10000 can be used without significant performance penalties.



### 5. **Neighborhood Functions**
The algorithm uses four neighborhood functions to generate new solutions during the optimization process. These functions modify the routes of snowplows in different ways to explore the solution space effectively:

1. **MK1 - Modify Route Avoiding Vertex**:
   - Randomly selects a machine and modifies its route by bypassing a randomly chosen intersection.
   - The "search depth" parameter determines how far the algorithm can go to find an alternative path. It is automatically adjusted by algorithm.

2. **MK2 - Reconstruct Route from Stage**:
   - Randomly selects a machine and a stage (excluding the first stage).
   - Reconstructs the route from the selected stage onward, ensuring that the new route prioritizes high-priority roads and avoids excessive looping.
   - The "param2" parameter controls the balance between avoiding repetitions and prioritizing critical roads. This parameter is controlled by the algorithm and changes according to temperature.

3. **SK1 - Generate Route from Least Frequent**:
   - Generates a route for a machine based on the least frequently used streets.
   - Uses the A* algorithm to find the most efficient path to street with highest danger level while minimizing the use of overutilized roads.
   - Ensures that the route maximizes the available time for each stage.

4. **SK2 - Change Path**:
   - Optimizes an existing route by removing costly, non-critical segments and replacing them with more efficient alternatives.
   - Focuses on real-time adjustments to ensure that the route adapts to current conditions (e.g., roads that have already been cleared).

These functions can be used individually, in combination, or all together, depending on the user's preferences and the complexity of the problem.



### 6. **Graphical Interface**
The project includes a simple, user-friendly graphical interface built with `tkinter`. Key features of the interface include:
- **Input Configuration**: Allows users to set up city layouts, snowfall predictions, and machine parameters.
- **Algorithm Control**: Provides options to adjust simulated annealing parameters (e.g., temperature, cooling rate, number of iterations).
- **Visualization**: Displays the optimized routes and key metrics (e.g., total time, machine utilization).



### 7. **Performance Considerations**
- **Graph Complexity**: The complexity of the road graph significantly impacts the algorithm's performance. For large, complex graphs (e.g., those generated with `OSMnx`), it is recommended to limit the number of iterations to avoid long computation times.
- **Scalability**: The algorithm is designed to handle up to six snowplows, but it can be extended to support more machines if needed.
- **Customizability**: Users can adjust the parameters and neighborhood functions to tailor the algorithm to specific scenarios or constraints.



## Installation and Usage
To run the project:
1. Clone the repository.
2. Install the required dependencies, preferably through provided `enviroment.yml` file.
3. Run the main script and configure the inputs via the graphical interface.



## Contributors
- [Mati00000](https://github.com/Mati00000): Implemented the two neighborhood functions, Graph class and integrated `OSMnx` library for our purpose.
- [PiotrekGrzyb](https://github.com/PiotrekGrzyb): Developed most of the graphical interface.
