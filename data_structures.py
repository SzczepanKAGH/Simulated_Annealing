import math
import matplotlib.pyplot as plt
import networkx as nx
from geopy.distance import geodesic


class Vertex:  # Obrazuje poczatek/koniec ulicy lub skrzyzowanie ulic
    def __init__(self, x, y, true_location=True):
        self.x = x
        self.y = y 
        self.neighbors = []  # Lista sąsiednich wierzcholkow
        self.true_location = true_location

    def add_neighbor(self, edge):
        if edge not in self.neighbors:  # Dodaj tylko jeśli nie ma jeszcze takiego sąsiada
            self.neighbors.append(edge)

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def __eq__(self, other):  # Pozwala porownac identycznosc dwoch wierzcholkow
        if isinstance(other, Vertex):
            return (self.x, self.y) == (other.x, other.y)
        return False

    def __lt__(self, other):
        return self.x + self.y < other.x + other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def get_distance(self, other):

        if self.true_location:
            coords_self = (self.y, self.x)  # (latitude, longitude) dla bieżącego punktu
            coords_other = (other.y, other.x)  # (latitude, longitude) dla punktu 'other'

            # Oblicz odległość geodezyjną między dwoma punktami
            return geodesic(coords_self, coords_other).meters / 1000  # Odległość w kilometrach

        else:
            return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class Edge:  # Obrazuje ulice polaczona przez dwa wierzcholki
    def __init__(self, start, end, priority=0, lanes=1, true_location=True):
        self.start = start
        self.end = end
        self.priority = priority   # priorytet w zakresie 0-100
        self.lanes = lanes  # ilosc pasow
        self.true_location = true_location
        self.snow_level = 0
        self.length = self.calculate_length()

    def calculate_length(self):
        return self.start.get_distance(self.end)

    def __repr__(self):
        return f"{self.start} -> {self.end}"

    def __eq__(self, other):
        # Uznajemy krawędzie za równe, jeśli mają takie same punkty, niezależnie od kierunku
        return (self.start == other.start and self.end == other.end) or \
               (self.start == other.end and self.end == other.start)

    def get_danger_level(self):
        return self.snow_level * self.priority * self.lanes
    
    def __hash__(self):
        # Hashowanie powinno uwzględniać tylko unikalne krawędzie, niezależnie od kierunku
        return hash((min(self.start, self.end), max(self.start, self.end)))


class Graph:  # Obrazuje pelny rozklad ulic/skrzyzowan
    def __init__(self, true_location=True):
        self.vertices = []
        self.edges = []
        self.baza = None  # Punkt początkowy (baza)
        self.true_location = true_location

    def add_base(self, x, y):
        # Sprawdzenie, czy wierzchołek o podanych współrzędnych już istnieje
        for vertex in self.vertices:
            if vertex.x == x and vertex.y == y:
                self.baza = vertex  # Ustaw bazę na istniejący wierzchołek
                return
            
        # Jeśli wierzchołek nie istnieje, dodaj nowy jako bazę
        self.baza = Vertex(x, y, self.true_location)
        self.vertices.append(self.baza)

    def add_vertex(self, x, y):
        # Sprawdzanie, czy wierzchołek o tych współrzędnych już istnieje
        for wierzcholek in self.vertices:
            if wierzcholek.x == x and wierzcholek.y == y:
                return wierzcholek  # Zwróć istniejący wierzchołek

        # Jeśli wierzchołek nie istnieje, stwórz nowy
        nowy_wierzcholek = Vertex(x, y, self.true_location)
        self.vertices.append(nowy_wierzcholek)
        return nowy_wierzcholek

    def get_edge(self, point1, point2):
        """
        Znajduje krawędź pomiędzy dwoma wierzchołkami (point1, point2).
        Zwraca krawędź, jeśli istnieje, w przeciwnym przypadku zwraca None.

        Args:
        - point1: krotka (x1, y1) reprezentująca pierwszy wierzchołek
        - point2: krotka (x2, y2) reprezentująca drugi wierzchołek

        Returns:
        - edge: Krawędź między wierzchołkami lub None, jeśli krawędź nie istnieje
        """
        # Jeśli point1 i point2 są obiektami Wierzcholek, przekształamy je na krotki
        if isinstance(point1, Vertex):
            point1 = (point1.x, point1.y)
        if isinstance(point2, Vertex):
            point2 = (point2.x, point2.y)

        for edge in self.edges:
            # Sprawdzamy, czy punkt1 jest początkiem krawędzi, a punkt2 końcem
            if (edge.start.x, edge.start.y) == point1 and (edge.end.x, edge.end.y) == point2:
                return edge

        return None  # Jeśli nie znaleziono krawędzi
    
    def get_edges_from_vertex(self, wierzcholek):
        """
        Zwraca listę krawędzi wychodzących z danego wierzchołka.
        """
        edges = []
        for edge in self.edges:
            if edge.start == wierzcholek:
                edges.append(edge)
        return edges

    def add_edge(self, punkt1, punkt2, priorytet, pasy):
        # Dodaje krawędź do grafu między punktami (x1, y1) a (x2, y2), uwzględniając kierunek.

        w1 = self.add_vertex(*punkt1)
        w2 = self.add_vertex(*punkt2)

        edge_1 = Edge(w1, w2, priorytet, pasy, self.true_location)
        self.edges.append(edge_1)

        edge_2 = Edge(w2, w1, priorytet, pasy, self.true_location)
        self.edges.append(edge_2)

        # Powiąż krawędź z wierzchołkami
        w1.add_neighbor(w2)
        w2.add_neighbor(w1)

    def __repr__(self):
        result = "Graf:\n"
        for edge in self.edges:
            result += f"  {edge}\n"
        return result
    
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------#
    #-----------------------------------------------------METODY DO RYSOWANIA GRAFU-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------#

    def draw(self, ax=None, size_x=10, size_y=10, show_coords=True, decimal_places=2, show_labels=True, node_size=600, label_font_size=10, edge_width=4, show_edge_labels=True):
        """
        Rysuje graf

        Parametry:
        - size_x, size_y: rozmiar wykresu.
        - show_coords: czy wyświetlać współrzędne węzłów.
        - decimal_places: do ilu miejsc po przecinku zaokrąglać współrzędne.
        - show_labels: czy wyświetlać etykiety węzłów.
        - node_size: rozmiar węzła.
        - label_font_size: wielkość czcionki etykiet węzłów.
        - edge_width: grubość linii (krawędzi).
        - show_edge_labels: czy wyświetlać tekst (etykiety) na krawędziach.
        """

        G = nx.Graph()

        # Dodaj wierzchołki do NetworkX
        for w in self.vertices:
            G.add_node((w.x, w.y))

        # Przygotuj słownik etykiet krawędzi
        edge_labels = {}
        for k in self.edges:
            G.add_edge((k.start.x, k.start.y), (k.end.x, k.end.y))
            # Etykieta krawędzi (np. priorytet, snow_level)
            edge_labels[((k.start.x, k.start.y), (k.end.x, k.end.y))] = f"Pr: {k.priority}, SL: {k.snow_level}"

        # Określamy pozycje węzłów (tutaj po prostu współrzędne x,y)
        pos = {(w.x, w.y): (w.x, w.y) for w in self.vertices}

        # Jeśli nie podano axes, tworzymy nowe okno
        if ax is None:
            plt.figure(figsize=(size_x, size_y))
            ax = plt.gca()

        # Rysowanie grafu (bez etykiet węzłów)
        # Ustawiamy 'width=edge_width', aby kontrolować grubość linii
        nx.draw(
            G,
            pos,
            ax=ax,
            with_labels=False,
            node_size=node_size,
            node_color='skyblue',
            edge_color='gray',
            width=edge_width
        )

        # Rysowanie etykiet krawędzi (o ile włączone show_edge_labels)
        if show_edge_labels:
            # Skaluj rozmiar czcionki etykiet krawędzi proporcjonalnie do edge_width
            # Bazowo było font_size=6 przy width=4, więc:
            edge_label_font_size = int(6 * (edge_width / 4))
            nx.draw_networkx_edge_labels(
                G,
                pos,
                edge_labels=edge_labels,
                font_size=edge_label_font_size,
                ax=ax
            )

        # Jeśli chcemy wyświetlać etykiety węzłów
        if show_labels:
            node_labels = {}
            for i, w in enumerate(self.vertices):
                if show_coords:
                    # Zaokrąglone współrzędne do 'decimal_places'
                    label_x = f"{w.x: .{decimal_places}f}"
                    label_y = f"{w.y: .{decimal_places}f}"
                    node_labels[(w.x, w.y)] = f"({label_x}, {label_y})"
                else:
                    # Nazwy W0, W1, W2... itp.
                    node_labels[(w.x, w.y)] = f"W{i}"

            nx.draw_networkx_labels(
                G,
                pos,
                labels=node_labels,
                font_size=label_font_size,
                font_color='black',
                ax=ax
            )

        # Rysowanie bazy (jeśli istnieje)
        if self.baza:
            ax.scatter(
                self.baza.x,
                self.baza.y,
                color='red',
                s=node_size * 1.25,
                label='Baza',
                edgecolors='red',
                facecolors='none',
                zorder=5,
                linewidth=3
            )

        ax.legend()

    def draw_with_solution(self, rozwiazanie: list, ax=None, size_x=10, size_y=10, show_coords=True, decimal_places=2, show_labels=True, node_size=600, label_font_size=10,
                           edge_width=2, show_edge_labels=True):
        """
        Rysuje graf z zaznaczeniem określonych krawędzi w rozwiązaniu.
        - rozwiazanie: lista list krawędzi (rozwiazanie dla jednej maszyny).
        - size_x, size_y: rozmiar wykresu.
        - show_coords: czy wyświetlać współrzędne węzłów.
        - decimal_places: do ilu miejsc po przecinku zaokrąglać współrzędne.
        - show_labels: czy wyświetlać etykiety węzłów.
        - node_size: rozmiar węzła.
        - label_font_size: wielkość czcionki etykiet węzłów.
        - edge_width: grubość linii krawędzi.
        - show_edge_labels: czy wyświetlać etykiety na krawędziach.
        """

        # Ustawienia kolorów dla etapów
        kolory_etapow = ['black', 'brown', 'green', 'blue', 'purple', 'red', 'pink', 'orange']
        stage_number = len(rozwiazanie)
        kolory_etapow = kolory_etapow * ((stage_number // len(kolory_etapow)) + 1)

        # Tworzenie grafu NetworkX
        G = nx.DiGraph()

        # Dodawanie wierzchołków
        for w in self.vertices:
            G.add_node((w.x, w.y))

        # Jeśli nie podano axes, tworzymy nowe okno
        if ax is None:
            plt.figure(figsize=(size_x, size_y))
            ax = plt.gca()

        # Dodawanie krawędzi z etykietami
        edge_labels = {}
        for k in self.edges:
            G.add_edge((k.start.x, k.start.y), (k.end.x, k.end.y))
            edge_labels[((k.start.x, k.start.y), (k.end.x, k.end.y))] = f"Pr: {k.priority}, SL: {k.snow_level}"

        # Pozycje węzłów
        pos = {(w.x, w.y): (w.x, w.y) for w in self.vertices}

        # Rysowanie podstawowego grafu z ustawioną grubością linii
        nx.draw(
            G, pos,
            ax=ax,
            with_labels=False,  # etykiety węzłów dodamy później
            node_size=node_size,
            node_color='skyblue',
            edge_color='gray',
            width=edge_width
        )

        # Rysowanie etykiet krawędzi, jeśli włączone
        if show_edge_labels:
            # Skalowanie font_size dla etykiet krawędzi proporcjonalnie do edge_width
            base_edge_font_size = 6  # podstawowy rozmiar czcionki przy width=2
            scaled_font_size = base_edge_font_size * (edge_width / 2)
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=scaled_font_size, ax=ax)

        # Rysowanie etykiet węzłów, jeśli włączone
        if show_labels:
            node_labels = {}
            for i, w in enumerate(self.vertices):
                if show_coords:
                    label_x = f"{w.x:.{decimal_places}f}"
                    label_y = f"{w.y:.{decimal_places}f}"
                    node_labels[(w.x, w.y)] = f"({label_x}, {label_y})"
                else:
                    node_labels[(w.x, w.y)] = f"W{i}"
            nx.draw_networkx_labels(
                G, pos,
                labels=node_labels,
                font_size=label_font_size,
                font_color='black',
                ax=ax
            )

        # Rysowanie zaznaczenia rozwiązań na drogach
        already_drawn_edges = set()
        for idx, etap in enumerate(rozwiazanie):
            kolor = kolory_etapow[idx % len(kolory_etapow)]
            grubosc = max(edge_width*3 - idx, edge_width / 2)  # dynamiczna grubość linii dla etapu
            for edge in etap:
                edge_tuple = (edge.start.x, edge.start.y, edge.end.x, edge.end.y)
                reverse_edge_tuple = (edge.end.x, edge.end.y, edge.start.x, edge.start.y)
                nx.draw_networkx_edges(
                    G, pos,
                    edgelist=[((edge.start.x, edge.start.y), (edge.end.x, edge.end.y))],
                    edge_color=kolor,
                    width=grubosc,
                    alpha=0.5,
                    arrows=True,
                    arrowstyle='-|>',
                    arrowsize=14,
                    ax=ax
                )
                already_drawn_edges.add(edge_tuple)
                already_drawn_edges.add(reverse_edge_tuple)

        # Rysowanie bazy (jeśli istnieje)
        if self.baza:
            ax.scatter(
                self.baza.x, self.baza.y,
                color='red', s=750, label='Baza', edgecolors='red',
                facecolors='none', zorder=5, linewidth=3
            )

        ax.legend()

