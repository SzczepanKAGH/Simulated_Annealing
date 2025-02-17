import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# List of plot data (global variable for updating in the function)
plots = []
current_plot = [0]  # Index of the current plot


def update_plot(ax, index):
    """Updates the plot based on the index."""
    plot = plots[index]
    ax.clear()
    ax.plot(plot["x"], plot["y"])
    ax.set_title(plot["title"])
    ax.set_ylabel(plot["ylabel"])
    ax.set_xlabel("Iteration")
    ax.grid(True)
    fig.canvas.draw()


def next_plot(event):
    """Switches to the next plot."""
    if current_plot[0] < len(plots) - 1:
        current_plot[0] += 1
        update_plot(ax, current_plot[0])


def prev_plot(event):
    """Switches to the previous plot."""
    if current_plot[0] > 0:
        current_plot[0] -= 1
        update_plot(ax, current_plot[0])


def plot_diagnostic_charts(danger, best_danger, temperature):
    """Draws interactive diagnostic charts."""
    global plots, fig, ax  # Reference to global variables

    # Update plot data
    plots = [
        {"title": "Danger level achieved in each iteration", "x": range(len(danger)), "y": danger,
         "ylabel": "Danger"},
        {"title": "Accepted danger level", "x": range(len(best_danger)), "y": best_danger,
         "ylabel": "Danger"},
        {"title": "Temperature", "x": range(len(temperature)), "y": temperature, "ylabel": ""},
    ]
    current_plot[0] = 0  # Reset plot index

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 7))
    plt.subplots_adjust(bottom=0.2)  # Space for buttons

    # Add buttons
    ax_prev = plt.axes((0.1, 0.05, 0.15, 0.075))  # Coordinates for the previous button
    ax_next = plt.axes((0.8, 0.05, 0.15, 0.075))  # Coordinates for the next button

    btn_prev = Button(ax_prev, "Previous")
    btn_next = Button(ax_next, "Next")

    btn_prev.on_clicked(prev_plot)
    btn_next.on_clicked(next_plot)

    # Draw the initial plot
    update_plot(ax, current_plot[0])

    # Display the interactive window
    plt.show(block=False)  # Do not block the program
    while plt.get_fignums():  # While there are open windows
        plt.pause(0.1)  # Update the GUI