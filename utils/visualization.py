import numpy as np
import torch
import math
import matplotlib.pyplot as plt
import seaborn as sns
from torchviz import make_dot
from IPython.display import display, clear_output

sns.set_style("darkgrid")


class LivePlot:
    """
    A class to plot live data in a Jupyter notebook.
    - How to use:
        import numpy as np
        live_plot = LivePlot(figsize=(10,5), groups=["train", "val"], use_seaborn=True)
        for i in range(10):
            y_train = np.random.rand()
            y_val = np.random.rand()
            live_plot.update({"train": y_train, "val": y_val}, display=True) ### or display=False and call live_plot.draw() later
    """
    def __init__(self, figsize=(10, 5), use_seaborn=False, groups=["default"]):
        """
        Params:
            figsize: tuple of int - example: (10, 5); default: (10, 5)
            use_seaborn: bool - example: True; default: False
            groups: list of str - example: ["train", "val"]; default: None
        """
        self.fig = None
        self.figsize = figsize
        self.groups = groups
        self.use_seaborn = use_seaborn
        self.history = {group_name: [] for group_name in self.groups}

    def setup_fig(self):
        self.fig = plt.figure(figsize=self.figsize)
        if self.groups is not None:
            n_rows = len(self.groups) // 2 + len(self.groups) % 2 if len(self.groups) > 1 else 1
            n_cols = 2 if len(self.groups) > 1 else 1
            self.group_axes = {group_name: self.fig.add_subplot(n_rows, n_cols, i+1) for i, group_name in enumerate(self.groups)}
        else:
            self.group_axes = {"default": self.fig.add_subplot(111)}

    def draw(self):
        if self.fig is None:
            self.setup_fig()
        for group_name, ax in self.group_axes.items():
            ax.cla()
            if self.use_seaborn:
                sns.lineplot(self.history[group_name], ax=ax)
            else:
                ax.plot(self.history[group_name])
            if group_name != "default":
                ax.set_title(group_name, fontsize=14, fontweight="bold")
            ax.set_xlabel("Timestep", fontsize=12)
        display(self.fig)
        clear_output(wait=True)

    def update(self, values, display=True, reset=False):
        """
        Params:
            values: dict of {group_name: y} OR float OR int - example: {"train": 0.5, "val": 0.6} OR 0.5 OR 5
                float or int will be added to the default group
            display: bool
        """
        if type(values) in (float, int):
            values = {"default": values}
        for group, y in values.items():
            if hasattr(y, "__iter__"):
                if reset:
                    self.history[group] = y
                else:
                    self.history[group].extend(y)
            else:
                if reset:
                    self.history[group] = [y]
                else:
                    self.history[group].append(y)
        if display:
            self.draw()

    def reset(self):
        self.history = {group_name: [] for group_name in self.history.keys()}


def resize_dot_graph(dot, size_per_element=0.15, min_size=12):
    """Resize the graph according to how much content it contains.
    Modify the graph in place.

    Author: ucalyptus (https://github.com/ucalyptus): https://github.com/szagoruyko/pytorchviz/issues/41#issuecomment-699061964
    """
    # Get the approximate number of nodes and edges
    num_rows = len(dot.body)
    content_size = num_rows * size_per_element
    size = max(min_size, content_size)
    size_str = str(size) + "," + str(size)
    dot.graph_attr.update(size=size_str)
    return dot


def get_model_dot(model, model_out, show_detailed_grad_info=True, output_filepath=None):
    if show_detailed_grad_info:
        dot = make_dot(model_out, params=dict(model.named_parameters()), show_attrs=True, show_saved=True)
    else:
        dot = make_dot(model_out, params=dict(model.named_parameters()))
    resize_dot_graph(dot, size_per_element=1, min_size=20)

    if output_filepath:
        dot.format = "png"
        dot.render(output_filepath)

    return dot


def show_imgs(imgs, titles=None):
    if len(imgs.shape) == 1: 
        imgs = imgs.reshape(1, int(math.sqrt(imgs.shape[0])), int(math.sqrt(imgs.shape[0]))) # flattened img -> square img
    if len(imgs.shape) == 2:
        imgs = imgs.reshape(imgs.shape[0], 1, int(math.sqrt(imgs.shape[1])), int(math.sqrt(imgs.shape[1]))) # flattened imgs -> square img
    
    fig, axes = plt.subplots(
        ((imgs.shape[0]-1) // 5) + 1, 5 if (len(imgs.shape) == 4 and imgs.shape[0] > 1) else 1,
        squeeze=False,
        figsize=(20, 4 * ((imgs.shape[0]-1) // 5 + 1))
    )
    curr_img_i = 0
    curr_img = imgs if len(imgs.shape) == 3 else imgs[curr_img_i]
    while curr_img != None:
        axes[curr_img_i // 5, curr_img_i % 5].imshow(np.transpose(curr_img, (1, 2, 0)))
        if type(titles) == str: axes[curr_img_i // 5, curr_img_i % 5].set_title(titles)
        if type(titles) in (list, tuple, set, torch.Tensor, np.ndarray): axes[curr_img_i // 5, curr_img_i % 5].set_title(titles[curr_img_i])
        curr_img_i += 1
        curr_img = None if (len(imgs.shape) == 3 or curr_img_i >= imgs.shape[0]) else imgs[curr_img_i]
    plt.show()


def get_umap_emb(x, n_umap_components=3):
    assert n_umap_components in (2, 3), "Use either 2 or 3 UMAP components (2D or 3D visualization)"
    import umap.umap_ as umap
    mapper = umap.UMAP(random_state=42, n_components=n_umap_components).fit(x)
    embedding = mapper.transform(x)
    return embedding


def scatter(x, y, dim=3, width=1000, height=600, color_label="digit", marker_size=2):
    assert dim in (2, 3), "Scatter plot supports only 2D and 3D."
    import plotly.express as px
    if dim == 2:
        fig = px.scatter(
            x,
            x=0, y=1,
            color=y,
            labels={'color': color_label},
            width=width,
            height=height
        )
    elif dim == 3:
        fig = px.scatter_3d(
            x, 
            x=0, y=1, z=2,
            color=y, 
            labels={"color": color_label},
            width=width,
            height=height
        )
    fig.update_traces(marker_size=marker_size)
    fig.show()
