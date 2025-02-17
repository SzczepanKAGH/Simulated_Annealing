from data_structures import Graph
import osmnx as ox
import math


def calculate_euclidean_distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def calculate_priority(edge_data, x_u, y_u, x_v, y_v, center_x, center_y, max_distance):
    """
    Returns edge priority considering road type and distance from center.

    Parameters:
    - edge_data: dictionary of OSM edge attributes
    - (x_u, y_u), (x_v, y_v): coordinates of edge nodes
    - (center_x, center_y): coordinates of area center
    - max_distance: maximum distance (e.g., radius) for coefficient interpolation

    Returns: priority in range 1-100
    """
    # 1. Base priority depending on road type
    highway_type = edge_data.get("highway", None)
    if isinstance(highway_type, list):
        highway_type = highway_type[0]

    mapping = {
        "motorway": 80,  # -> Highway, multi-lane, grade-separated
        "trunk": 75,  # -> Expressway or other major arterial (lower rank than motorway)
        "primary": 70,  # -> Main road (e.g., national road)
        "secondary": 60,  # -> Medium-rank road (e.g., state road)
        "tertiary": 50,  # -> County road or local connecting road
        "residential": 40,  # -> Road in residential area
        "service": 30,  # -> Service road, e.g., access to parking lots, gas stations
    }
    base_priority = mapping.get(highway_type, 20)

    # 2. Calculate edge midpoint and distance to center
    mid_x = (x_u + x_v) / 2.0
    mid_y = (y_u + y_v) / 2.0
    distance_mid = calculate_euclidean_distance(mid_x, mid_y, center_x, center_y)

    # 3. Interpolate distance-dependent coefficient
    max_coeff = 1.5
    min_coeff = 0.5
    # If distance greater than or equal to max_distance, set minimum coefficient
    if distance_mid >= max_distance:
        factor = min_coeff
    else:
        # Linear interpolation: closer to center → coefficient closer to max_coeff, further → closer to min_coeff
        factor = max_coeff - ((max_coeff - min_coeff) * (distance_mid / max_distance))

    # 4. Calculate final priority and clip to range 1-100
    final_priority = base_priority * factor
    if final_priority < 1:
        final_priority = 1
    elif final_priority > 100:
        final_priority = 100

    return int(final_priority)


def calculate_lanes(edge_data):
    """
    Function to get number of lanes from OSM 'lanes' attribute.
    Returns 1 if no data available.
    """
    lanes = edge_data.get("lanes", 1)
    if isinstance(lanes, list):
        lanes = lanes[0]  # sometimes it's a list

    try:
        return int(lanes)
    except (ValueError, TypeError):
        return 1


def get_osm_graph_from_point(center_point, dist=800, dist_type="bbox", network_type="drive", main_roads=False,
                             custom_roads=None):
    """
    Retrieves map section from OSM around given point (center_point)
    within radius dist (in meters) and creates a 'Graph' object.

    Parameters:
    - center_point: (lat, lon) - center point
    - dist: radius in meters (or half side if dist_type='bbox')
    - dist_type: 'bbox', 'circle' or 'network' (buffer type)
    - network_type: 'drive', 'walk', 'bike' etc.
    - main_roads: bool, if True -> retrieve only main road categories
    - custom_roads: list of strings, e.g., ["motorway", "primary", "secondary"], for custom filter

    Returns: 'Graph' object
    """

    # Determine if we build custom_filter
    #    - if main_roads=True, use predetermined set of major roads
    #    - if custom_roads is provided, build filter from that list
    #    - otherwise None (OSMnx will fetch according to default 'network_type')

    if custom_roads and isinstance(custom_roads, list) and len(custom_roads) > 0:
        # Build expression e.g.: '["highway"~"motorway|primary|secondary"]'
        filter_str = "|".join(custom_roads)
        custom_filter = f'["highway"~"{filter_str}"]'
    elif main_roads:
        # Example: motorway, primary, secondary, trunk, tertiary
        custom_filter = '["highway"~"motorway|trunk|primary|secondary|trunk|tertiary"]'
    else:
        # No filter
        custom_filter = None

    G_osm = ox.graph_from_point(
        center_point,
        dist=dist,
        dist_type=dist_type,
        network_type=network_type,
        custom_filter=custom_filter
    )

    graph = Graph()

    # add base
    if len(G_osm.nodes) > 0:
        first_node_id = list(G_osm.nodes)[0]
        x_base = G_osm.nodes[first_node_id]["x"]
        y_base = G_osm.nodes[first_node_id]["y"]
        graph.add_base(x_base, y_base)

    center_lat, center_lon = center_point
    max_distance = dist
    for u, v, key, data in G_osm.edges(keys=True, data=True):
        x_u = G_osm.nodes[u]["x"]
        y_u = G_osm.nodes[u]["y"]
        x_v = G_osm.nodes[v]["x"]
        y_v = G_osm.nodes[v]["y"]

        priority = calculate_priority(data, x_u, y_u, x_v, y_v, center_lon, center_lat, max_distance)
        lanes = calculate_lanes(data)

        graph.add_edge((x_u, y_u), (x_v, y_v), priority, lanes)

    return graph


# Function to load a graph from a given street layout file 'street_layout.txt',
# where the data is represented in the following format:
# (vertex_1) (vertex_2) priority lanes

def load_graph_from_file(filename):
    graph = Graph(true_location=False)  # Create an empty graph

    with open(filename, 'r') as file:
        lines = file.readlines()  # Read all lines from the file

        # Check if the line is not empty
        lines = [line.strip() for line in lines if line.strip()]

        # Treat the first point as the base
        first_line = lines[0]
        start_point, end_point, priority, lanes = first_line.split(" ")
        start_point = eval(start_point)  # Convert e.g., "(0, 0)" to a tuple (0, 0)
        end_point = eval(end_point)
        priority = int(priority)
        lanes = int(lanes)

        graph.add_edge(start_point, end_point, priority, lanes)
        graph.add_base(*start_point)  # Add the base

        # Process the remaining lines - load the rest of the streets
        for line in lines[1:]:
            try:
                start_point, end_point, priority, lanes = line.split(" ")
                start_point = eval(start_point)
                end_point = eval(end_point)
                priority = int(priority)
                lanes = int(lanes)

                graph.add_edge(start_point, end_point, priority, lanes)
            except ValueError as e:
                print(f"Invalid format in line: '{line}'. Error: {e}")
                continue  # Ignore the invalid line

    return graph  # Return the completed graph


def get_graph_of_city(city_name: str, **kwargs):
    city_loc_dict = {
        "Krakow": (50.062756, 19.938077),
        "Kety": (49.88335218571101, 19.22146813090962),
        "Warsaw": (52.2303067675569, 20.984324785193277),
        "Gdansk": (54.35163704525984, 18.646516947567964),
        "Wroclaw": (51.11719673027559, 17.007465255279378),
        "Poznan": (52.41008135266712, 16.929575089709026),
        "Sandomierz": (50.687756998444975, 21.732591122191614)
    }

    return get_osm_graph_from_point(city_loc_dict[city_name], **kwargs)