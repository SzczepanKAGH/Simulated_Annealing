import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from map_import import load_graph_from_file
from solution import RoadClearingProblem, Machine
from diagnostics import plot_diagnostic_charts
from map_import import get_graph_of_city

class RoadClearingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Road Clearing Optimization")
        self.root.geometry("1700x950")
        self.root.configure(bg='white')
        self.root.resizable(True, True)

        # Configure grid weight for main window
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Styling
        style = ttk.Style()
        style.configure("TFrame", background="white")
        style.configure("TLabel", background="white", foreground="black", font=("Arial", 10))
        style.configure("TButton", background="#DDD", foreground="black", font=("Arial", 10))
        style.configure("Remove.TButton", background="#FF5555", foreground="white", font=("Arial", 10, "bold"))
        style.configure("Start.TButton", background="#555", foreground="black", font=("Arial", 12, "bold"), padding=10)
        style.configure("TEntry", background="#333", foreground="black")

        # Main container frame using grid
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=3)  # Right frame gets more space
        main_frame.grid_columnconfigure(0, weight=1)  # Left frame gets less space

        # Create a frame for the left side that will contain the canvas and scrollbar
        left_container = ttk.Frame(main_frame)
        left_container.grid(row=0, column=0, sticky="nsew")
        left_container.grid_rowconfigure(0, weight=1)
        left_container.grid_columnconfigure(0, weight=1)

        # Create canvas and scrollbar for left panel
        self.left_canvas = tk.Canvas(left_container, bg='white')
        left_scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=self.left_canvas.yview)

        # Left frame (controls) - now inside canvas
        left_frame = ttk.Frame(self.left_canvas)

        # Configure scroll region when left frame changes
        left_frame.bind('<Configure>', lambda e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all")))

        # Create window inside canvas for left frame
        self.left_canvas.create_window((0, 0), window=left_frame, anchor="nw", width=left_container.winfo_reqwidth())

        # Configure canvas scroll
        self.left_canvas.configure(yscrollcommand=left_scrollbar.set)

        # Pack canvas and scrollbar into left container
        self.left_canvas.grid(row=0, column=0, sticky="nsew")
        left_scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure left frame grid
        left_frame.grid_columnconfigure(0, weight=1)

        # Right frame (graph)
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # Graph frame
        self.graph_frame = ttk.Frame(right_frame)
        self.graph_frame.grid(row=0, column=0, sticky="nsew")
        self.graph_frame.grid_rowconfigure(0, weight=1)
        self.graph_frame.grid_columnconfigure(0, weight=1)

        # Create navigation frame below the graph
        self.nav_frame = ttk.Frame(right_frame)
        self.nav_frame.grid(row=1, column=0, sticky="ew", pady=5)

        # Navigation buttons and label
        self.prev_button = ttk.Button(self.nav_frame, text="←", command=self.show_previous_solution, state="disabled")
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.solution_label = ttk.Label(self.nav_frame, text="")
        self.solution_label.pack(side=tk.LEFT, padx=20)

        self.next_button = ttk.Button(self.nav_frame, text="→", command=self.show_next_solution, state="disabled")
        self.next_button.pack(side=tk.LEFT, padx=5)

        self.figure = plt.Figure(figsize=(10, 5))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self.graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Initialize solution-related attributes
        self.current_solution_index = 0
        self.solutions = None

        # Button frame
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=0, column=0, sticky="ew", pady=5)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.load_file_button = ttk.Button(button_frame, text="Load from txt file", command=self.load_file)
        self.load_file_button.grid(row=0, column=0, padx=2, sticky="ew")

        self.choose_location_button = ttk.Button(button_frame, text="Choose location", command=self.choose_location)
        self.choose_location_button.grid(row=0, column=1, padx=2, sticky="ew")

        self.selected_city_label = ttk.Label(left_frame, text="Selected city: ")
        self.selected_city_label.grid(row=1, column=0, pady=5, sticky="w")

        # Parameters frame
        params_frame = ttk.Frame(left_frame)
        params_frame.grid(row=2, column=0, sticky="ew", pady=5)
        params_frame.grid_columnconfigure(0, weight=1)

        # Parameters widgets
        current_row = 0

        self.time_between_label = ttk.Label(params_frame, text="Time between snowfalls:")
        self.time_between_label.grid(row=current_row, column=0, sticky="w", pady=2)
        current_row += 1
        self.time_between_entry = ttk.Entry(params_frame)
        self.time_between_entry.grid(row=current_row, column=0, sticky="ew", pady=2)
        current_row += 1

        self.snowfall_label = ttk.Label(params_frame, text="Snowfall forecast (e.g., [3,4,5,6]):")
        self.snowfall_label.grid(row=current_row, column=0, sticky="w", pady=2)
        current_row += 1
        self.snowfall_entry = ttk.Entry(params_frame)
        self.snowfall_entry.grid(row=current_row, column=0, sticky="ew", pady=2)
        current_row += 1

        self.temperature_label = ttk.Label(params_frame, text="Temperature:")
        self.temperature_label.grid(row=current_row, column=0, sticky="w", pady=2)
        current_row += 1
        self.temperature_entry = ttk.Entry(params_frame)
        self.temperature_entry.grid(row=current_row, column=0, sticky="ew", pady=2)
        current_row += 1

        self.cooling_rate_label = ttk.Label(params_frame, text="Cooling rate (0.95 - 0.99):")
        self.cooling_rate_label.grid(row=current_row, column=0, sticky="w", pady=2)
        current_row += 1
        self.cooling_rate_entry = ttk.Entry(params_frame)
        self.cooling_rate_entry.grid(row=current_row, column=0, sticky="ew", pady=2)
        current_row += 1

        self.max_iterations_label = ttk.Label(params_frame, text="Maximum iterations:")
        self.max_iterations_label.grid(row=current_row, column=0, sticky="w", pady=2)
        current_row += 1
        self.max_iterations_entry = ttk.Entry(params_frame)
        self.max_iterations_entry.grid(row=current_row, column=0, sticky="ew", pady=2)

        # Machine list frame
        self.machine_list_frame = ttk.LabelFrame(left_frame, text='Machine Management', padding=10)
        self.machine_list_frame.grid(row=3, column=0, sticky="nsew", pady=10)
        self.machine_list_frame.grid_rowconfigure(0, weight=1)
        self.machine_list_frame.grid_columnconfigure(0, weight=1)

        # Scrollable machine list
        self.machine_canvas = tk.Canvas(self.machine_list_frame)
        self.machine_scrollbar = ttk.Scrollbar(self.machine_list_frame, orient=tk.VERTICAL,
                                               command=self.machine_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.machine_canvas)

        self.scrollable_frame.bind("<Configure>",
                                   lambda e: self.machine_canvas.configure(
                                       scrollregion=self.machine_canvas.bbox("all")))

        self.machine_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.machine_canvas.configure(yscrollcommand=self.machine_scrollbar.set)

        self.machine_canvas.grid(row=0, column=0, sticky="nsew")
        self.machine_scrollbar.grid(row=0, column=1, sticky="ns")

        self.machine_list = []

        # Add machine button
        self.add_machine_button = ttk.Button(left_frame, text="Add Machine", command=self.add_machine)
        self.add_machine_button.grid(row=4, column=0, sticky="ew", pady=5)

        # Neighborhood methods frame
        self.neighborhood_methods = {
            "MK1": 0,
            "MK2": 1,
            "SK1": 2,
            "SK2": 3
        }

        self.neighborhood_choices = {}
        self.neighborhood_frame = ttk.LabelFrame(left_frame, text='Select Neighborhood Methods',
                                                 padding=10)
        self.neighborhood_frame.grid(row=5, column=0, sticky="ew", pady=10)

        for i, method in enumerate(self.neighborhood_methods.keys()):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(self.neighborhood_frame, text=method, variable=var)
            chk.grid(row=i, column=0, sticky="w")
            self.neighborhood_choices[method] = var

        # Start button
        self.start_button = ttk.Button(left_frame, text="Start", command=self.run_optimization, style="Start.TButton")
        self.start_button.grid(row=6, column=0, sticky="ew", pady=15)

        # Graph frame
        self.graph_frame = ttk.Frame(right_frame)
        self.graph_frame.grid(row=0, column=0, sticky="nsew")
        self.graph_frame.grid_rowconfigure(0, weight=1)
        self.graph_frame.grid_columnconfigure(0, weight=1)

        self.figure = plt.Figure(figsize=(10, 5))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self.graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)

        # Bind mouse wheel to both main left panel and machine list scrolling
        self.bind_mouse_wheel(left_frame)

    def bind_mouse_wheel(self, widget):
        """Recursively bind mouse wheel to all widgets"""
        widget.bind("<MouseWheel>", self.on_mouse_wheel)
        widget.bind("<Button-4>", self.on_mouse_wheel)
        widget.bind("<Button-5>", self.on_mouse_wheel)
        for child in widget.winfo_children():
            self.bind_mouse_wheel(child)

    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 5 or event.delta == -120:  # Scroll down
            self.left_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120:  # Scroll up
            self.left_canvas.yview_scroll(-1, "units")
        return "break"  # Prevent event propagation

    def on_window_resize(self, event):
        if hasattr(self, 'figure') and event.widget == self.root:
            # Update canvas width to match container
            self.left_canvas.itemconfig(1, width=event.width // 4)  # Adjust divisor as needed

            # Update graph size
            width = self.graph_frame.winfo_width() / 100
            height = self.graph_frame.winfo_height() / 100
            self.figure.set_size_inches(width, height)
            self.canvas.draw()

    def choose_location(self):
        city_window = tk.Toplevel(self.root)
        city_window.title("Choose City")
        city_window.geometry("350x300")
        tk.Label(city_window, text="Choose city:", font=("Arial", 12)).pack(pady=10)

        cities = ["Warsaw", "Krakow", "Wroclaw", "Poznan", "Gdansk", "Sandomierz", "Kety"]
        self.selected_city = tk.StringVar(value=cities[0])

        for city in cities:
            tk.Radiobutton(city_window, text=city, variable=self.selected_city, value=city).pack(anchor='w')

        def set_city():
            self.selected_city_label.config(text=f"Selected city: {self.selected_city.get()}")
            city_window.destroy()
            self.root.update_idletasks()
            city_window.destroy()

            try:
                self.road_graph = get_graph_of_city(self.selected_city.get(), custom_roads=["tertiary", "residential"])
                print("Graph loaded")
                self.draw_graph()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load graph: {e}")

        ttk.Button(city_window, text="OK", command=set_city).pack(pady=10)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                self.road_graph = load_graph_from_file(file_path)
                print("Graph loaded")
                self.draw_graph()
                messagebox.showinfo("Success", "File loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load graph: {e}")

    def draw_graph(self):
        if not hasattr(self, 'road_graph'):
            messagebox.showerror("Error", "Graph not loaded.")
            return

        self.ax.clear()
        self.road_graph.draw(ax=self.ax, show_labels=False, show_edge_labels=False, node_size=50, edge_width=2)
        self.canvas.draw()

    def add_machine(self):
        if len(self.machine_list) >= 7:
            messagebox.showwarning("Limit reached", "Cannot add more than 7 machines.")
            return
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill=tk.X, pady=2)
        label = ttk.Label(frame, text=f"Machine {len(self.machine_list) + 1} - Speed (km/h):")
        label.pack(side=tk.LEFT)
        entry = ttk.Entry(frame, width=5, font=("Arial", 10), justify='center', foreground='black')
        entry.pack(side=tk.LEFT, padx=5)
        remove_button = tk.Button(frame, text="X", command=lambda: self.remove_machine(frame), bg='red', fg='white', font=("Arial", 10, "bold"))
        remove_button.pack(padx=0)
        self.machine_list.append((frame, label, entry, remove_button))
        self.scrollable_frame.update_idletasks()
        self.machine_canvas.configure(scrollregion=self.machine_canvas.bbox("all"))

    def remove_machine(self, frame):
        frame.destroy()
        self.machine_list = [m for m in self.machine_list if m[0] != frame]
        self.scrollable_frame.update_idletasks()
        self.machine_canvas.configure(scrollregion=self.machine_canvas.bbox("all"))

    def run_optimization(self):
        if not hasattr(self, 'road_graph') or self.road_graph is None:
            messagebox.showerror("Error", "First load a file with the street layout.")
            return

        try:
            Tmax = int(self.time_between_entry.get())
            max_iterations = int(self.max_iterations_entry.get())
            snowfall_forecast = list(map(int, self.snowfall_entry.get().strip('[]').split(',')))
            temperature = float(self.temperature_entry.get())
            cooling_rate = float(self.cooling_rate_entry.get())

            machines = []
            for frame, label, entry, remove_button in self.machine_list:
                try:
                    speed = float(entry.get())
                    machines.append(Machine(speed=speed))
                except ValueError:
                    messagebox.showerror("Error", "Enter valid speed values for all machines.")
                    return

            selected_methods = [key for key, var in self.neighborhood_choices.items() if var.get()]
            if not selected_methods:
                messagebox.showerror("Error", "Select at least one neighborhood method.")
                return

            # Load neighborhood functions
            neighborhood_functions = [self.neighborhood_methods[method] for method in selected_methods]

            problem = RoadClearingProblem(snowfall_forecast, self.road_graph, machines, Tmax)
            best_solution, best_danger, diagnostics = problem.simulated_annealing(
                initial_temperature=temperature,
                cooling_rate=cooling_rate,
                max_iterations=max_iterations,
                choose_neighbour_function=neighborhood_functions
            )

            messagebox.showinfo("Optimization complete", f"Best danger level: {best_danger}")

            self.visualize_solution(diagnostics, best_solution)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to run optimization: {e}")

    def show_previous_solution(self):
        if self.solutions and self.current_solution_index > 0:
            self.current_solution_index -= 1
            self.update_solution_visualization()

    def show_next_solution(self):
        if self.solutions and self.current_solution_index < len(self.solutions) - 1:
            self.current_solution_index += 1
            self.update_solution_visualization()

    def update_solution_visualization(self):
        if not self.solutions:
            return

        # Clear previous plot
        self.ax.clear()

        # Draw the current solution
        self.road_graph.draw_with_solution(
            self.solutions[self.current_solution_index].route,
            ax=self.ax,
            show_labels=False,
            show_edge_labels=False,
            node_size=50,
            edge_width=2
        )

        # Update the canvas
        self.canvas.draw()

        # Update the solution label
        self.solution_label.config(
            text=f"Route {self.current_solution_index + 1} of {len(self.solutions)}"
        )

        # Update button states
        self.prev_button.config(state="normal" if self.current_solution_index > 0 else "disabled")
        self.next_button.config(state="normal" if self.current_solution_index < len(self.solutions) - 1 else "disabled")

    def visualize_solution(self, diagnostics, solution):
        if not solution:
            return

        # Store the solutions
        self.solutions = solution
        self.current_solution_index = 0

        # Enable navigation buttons if there are multiple solutions
        if len(solution) > 1:
            self.next_button.config(state="normal")

        # Update the visualization
        self.update_solution_visualization()

        # Show diagnostic charts in a new window
        plot_diagnostic_charts(*diagnostics)

if __name__ == "__main__":
    root = tk.Tk()
    app = RoadClearingApp(root)
    root.mainloop()
