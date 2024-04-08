import matplotlib.pyplot as plt
import numpy as np

from flasc.utilities.utilities_examples import load_floris_artificial as load_floris
from flasc.visualization import (
    plot_floris_layout,
    plot_layout_only,
    plot_layout_with_waking_directions,
    shade_region,
)

# Example demonstrates some methods for visualizing the layout of the farm
# represented within the FLORIS interface


if __name__ == "__main__":
    # Set up FLORIS interface
    print("Initializing the FLORIS object for our demo wind farm")
    fm, _ = load_floris()

    # Defines alternative names for each turbine with 1-index
    turbine_names = ["Turbine-%d" % (t + 1) for t in range(len(fm.layout_x))]

    # Plot using default 0-indexed labels (includes power/thrust curve)
    plot_floris_layout(fm, plot_terrain=False)

    # Plot using default given 1-indexed labels (includes power/thrust curve)
    plot_floris_layout(fm, plot_terrain=False, turbine_names=turbine_names)

    # Plot only the layout with default options
    plot_layout_only(fm)

    # Plot only the layout with custom options
    plot_layout_only(fm, {"turbine_names": turbine_names, "color": "g"})

    # Plot layout with wake directions and inter-turbine distances labeled
    plot_layout_with_waking_directions(fm)

    # Plot layout with wake directions and inter-turbine distances labeled
    # (using custom options)
    plot_layout_with_waking_directions(
        fm,
        limit_num=3,  # limit to 3 lines per turbine
        layout_plotting_dict={
            "turbine_names": turbine_names,
            "turbine_indices": range(2, len(fm.layout_x)),
        },
        wake_plotting_dict={"color": "r"},
    )

    # Demonstrate shading of an arbitrary region
    points_for_demo = np.array([[600, 0], [1400, 0], [1200, 1000]])
    ax = plot_layout_only(fm)
    shade_region(
        points_for_demo,
        show_points=True,
        plotting_dict_region={"color": "blue", "label": "Example region"},
        plotting_dict_points={"color": "blue", "marker": "+", "s": 50},
        ax=ax,
    )

    plt.show()
