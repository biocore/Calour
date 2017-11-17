# ----------------------------------------------------------------------------
# Copyright (c) 2016--,  Calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from logging import getLogger
import importlib
import itertools

import matplotlib as mpl
import matplotlib.patches as mpatches
import numpy as np

from .. import Experiment
from ..database import _get_database_class
from .._dendrogram import plot_tree
from ..util import _to_list, _transition_index


logger = getLogger(__name__)


def _create_plot_gui(exp, gui='cli', databases=('dbbact',), tree_size=0):
    '''Create plot GUI object.

    It still waits for the heatmap to be plotted and set up.

    Parameters
    ----------
    gui : str or None (optional)
        If None, just plot a simple matplotlib figure with the heatmap and no interactive elements.
        is str, name of the gui module to use for displaying the heatmap. options:
        'cli' (default) : just cli information about selected sample/feature.
        'qt5' : gui using QT5 (with full dbBact interface)
        'jupyter' : gui for Jupyter notebooks (using widgets)
        Other string : name of child class of plotgui (which should reside in heatmap/lower(classname).py)
    databases : list of str (optional)
        Names of the databases to use to obtain info about sequences. options:
        'dbbact' : the dbBact manual annotation database
        'spongeworld' : the sponge microbiome automatic annotation database
        'redbiom' : the automatic qiita database

    Returns
    -------
    ``PlotGUI`` or its child class
    '''
    # load the gui module to handle gui events & link with annotation databases
    possible_gui = {'qt5': 'PlotGUI_QT5', 'cli': 'PlotGUI_CLI', 'jupyter': 'PlotGUI_Jupyter'}
    if gui in possible_gui:
        gui = possible_gui[gui]
    else:
        raise ValueError('Unknown GUI specified: %r. Possible values are: %s' % (gui, list(possible_gui.keys())))
    gui_module_name = 'calour.heatmap.' + gui.lower()
    gui_module = importlib.import_module(gui_module_name)
    GUIClass = getattr(gui_module, gui)
    gui_obj = GUIClass(exp, tree_size=tree_size)

    # link gui with the databases requested
    for cdatabase in databases:
        cdb = _get_database_class(cdatabase, exp=exp)
        gui_obj.databases.append(cdb)
        # select the database for use with the annotate button
        if cdb.annotatable:
            if gui_obj._annotation_db is None:
                gui_obj._annotation_db = cdb
            else:
                logger.warning(
                    'More than one database with annotation capability.'
                    'Using first database (%s) for annotation'
                    '.' % gui_obj._annotation_db.database_name)
    return gui_obj


def _truncate_middle(x, length=16):
    '''convert to str and truncate the mid-part of the strings if they are too long. '''
    y = [str(i) for i in x]
    if length is None:
        # don not truncate
        return y
    else:
        # minus 2 dots
        mid = (length - 2) // 2
        return ['%s..%s' % (i[:mid], i[-mid:]) if len(i) > length else i for i in y]


def _set_axis_ticks(ax, which, ticklabels, tickmax, n, kwargs, ticklabel_len):
    '''Plot tick and ticklabels of x or y axis.

    Parameters mean axes, x or y axis, list of tick labels, max number
    of ticks, the upper bound of xlim/ylim, dict passing as text
    property, the length of each tick label.

    '''
    ticks = _transition_index(ticklabels)
    tick_pos, tick_val = zip(*ticks)

    axis = getattr(ax, which + 'axis')

    if tickmax is None:
        # show all labels
        tickmax = n
    # should be not larger than maxticks
    tickmax = min(tickmax, mpl.ticker.Locator.MAXTICKS)
    if len(tick_pos) <= tickmax:
        tick_pos = np.array([0.] + list(tick_pos))
        # samples position - 0.5 before and go to 0.5 after
        tick_pos -= 0.5
        for pos in tick_pos[1:-1]:
            if which == 'x':
                method = 'axvline'
            elif which == 'y':
                method = 'axhline'
            else:
                raise ValueError('Unknow axis: %r.' % which)
            getattr(ax, method)(pos, color='white', linewidth=1)

        # set tick/label at the middle of each sample group
        axis.set_ticks(tick_pos[:-1] + (tick_pos[1:] - tick_pos[:-1]) / 2)
        axis.set_ticklabels(_truncate_middle(tick_val, ticklabel_len))
    else:
        def format_fn(tick_val, tick_pos):
            # cf http://matplotlib.org/gallery/ticks_and_spines/tick_labels_from_values.html
            if 0 <= tick_val < n:
                return ticklabels[int(tick_val)]
            else:
                return ''
        # set the maximal number of feature labels
        axis.set_major_formatter(mpl.ticker.FuncFormatter(format_fn))
        axis.set_major_locator(mpl.ticker.MaxNLocator(tickmax, integer=True))
    if kwargs is None:
        kwargs = {'rotation': 45, 'ha': 'right'}
    for t in axis.get_ticklabels():
        t.set(**kwargs)


def heatmap(exp: Experiment, sample_field=None, feature_field=None,
            xticklabel_kwargs=None, yticklabel_kwargs=None,
            xticklabel_len=16, yticklabel_len=16,
            xticks_max=10, yticks_max=30,
            clim=(None, None), cmap='viridis', norm=mpl.colors.LogNorm(),
            title=None, rect=None, cax=None, ax=None):
    '''Plot a heatmap for the experiment.

    Plot either a simple heatmap for the experiment with features in row
    and samples in column.

    .. note:: By default it log transforms the abundance values and then plot heatmap.
       The original object is not modified.

    Parameters
    ----------
    sample_field : str or ``None`` (optional)
        The field of sample metadata to display on the x-axis or None (default) to not show x axis.
    feature_field : str or ``None`` (optional)
        The field of feature meadata to display on the y-axis or None (default) to not show y axis.
    xticklabel_kwargs, yticklabel_kwargs : dict or None (optional)
        keyword arguments passing as properties to :class:`matplotlib.text.Text` for
        tick labels on x axis and y axis. As an example,
        ``xticklabel_kwargs={'color': 'r', 'ha': 'center', 'rotation': 90,
        'family': 'serif', 'size'=7}``
    xticklabel_len, yticklabel_len : int or ``None``
        The maximal length for the tick labels on x axis and y axis (will be cut to
        this length if longer). Used to prevent long labels from
        taking too much space. None indicates no shortening
    xticks_max, yticks_max : int or ``None``
        max number of ticks to render on the heatmap. If ``None``,
        allow all ticks for each sample (xticks_max) or feature (yticks_max) in the table,
        which can be very slow if there are a large number of samples or features.
    clim : tuple of (float, float), optional
        the min and max values for the heatmap color limits. It uses the min
        and max values in the input :attr:`.Experiment.data` array by default.
    cmap : str or :class:`matplotlib.colors.ListedColormap`
        str to indicate the colormap name. Default is "viridis" colormap.
        For all available colormaps in matplotlib: https://matplotlib.org/users/colormaps.html
    norm : :class:`matplotlib.colors.Normalize` or ``None``
        passed to ``norm`` parameter of :func:`matplotlib.pyplot.imshow`. Default is log scale.
    title : None or str (optional)
        None (default) to not show title. str to set title to str.
    rect : tuple of (int, int, int, int) or None (optional)
        None (default) to set initial zoom window to the whole experiment.
        [x_min, x_max, y_min, y_max] to set initial zoom window
    cax : :class:`matplotlib.axes.Axes`, optional
        The axes where a legend colorbar for the heatmap is plotted.
    ax : :class:`matplotlib.axes.Axes` or ``None`` (default), optional
        The axes where the heatmap is plotted. None (default) to create a new figure and
        axes to plot the heatmap

    Returns
    -------
    :class:`matplotlib.axes.Axes` of the heatmap


    Examples
    --------
    .. plot::

       Let's create a very simple data set:

       >>> from calour import Experiment
       >>> import matplotlib as mpl
       >>> import pandas as pd
       >>> from matplotlib import pyplot as plt
       >>> exp = Experiment(np.array([[0,9], [7, 4]]), sparse=False,
       ...                  sample_metadata=pd.DataFrame({'category': ['A', 'B'],
       ...                                                'ph': [6.6, 7.7]},
       ...                                               index=['s1', 's2']),
       ...                  feature_metadata=pd.DataFrame({'motile': ['y', 'n']}, index=['otu1', 'otu2']))

       Let's then plot the heatmap:

       >>> fig, ax = plt.subplots()
       >>> exp.heatmap(sample_field='category', feature_field='motile', title='Fig 1 log scale', ax=ax)   # doctest: +SKIP

       By default, the color is plot in log scale. Let's say we would like to plot heatmap in normal scale instead of log scale:

       >>> fig, ax = plt.subplots()
       >>> norm = mpl.colors.Normalize()
       >>> exp.heatmap(sample_field='category', feature_field='motile', title='Fig 2 normal scale',
       ...             norm=norm, ax=ax)             # doctest: +SKIP

       Let's say we would like to show the presence/absence of each
       OTUs across samples in heatmap. And we define presence as
       abundance larger than 4:

       >>> expbin = exp.binarize(4)
       >>> expbin.data
       array([[0, 1],
              [1, 0]])

       Now we have converted the abundance table to the binary
       table. Let's define a binary color map and use it to plot the
       heatmap:

       >>> # define the colors
       >>> cmap = mpl.colors.ListedColormap(['r', 'k'])
       >>> # create a normalize object the describes the limits of each color
       >>> norm = mpl.colors.BoundaryNorm([0., 0.5, 1.], cmap.N)
       >>> fig, ax = plt.subplots()
       >>> expbin.heatmap(sample_field='category', feature_field='motile', title='Fig 3 binary',
       ...                cmap=cmap, norm=norm, ax=ax)         # doctest: +SKIP

    '''
    logger.debug('Plot heatmap')
    # import pyplot is less polite. do it locally
    import matplotlib.pyplot as plt

    data = exp.get_data(sparse=False)
    numrows, numcols = exp.shape

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()

    if title is not None:
        ax.set_title(title)
    # set the initial zoom window if supplied
    if rect is not None:
        ax.set_xlim(rect[0], rect[1])
        ax.set_ylim(rect[2], rect[3])

    # init the default colormap
    if cmap is None:
        cmap = plt.rcParams['image.cmap']
    if isinstance(cmap, str):
        cmap = plt.get_cmap(cmap)
    # this set cells of zero value.
    cmap.set_bad('black')

    # plot the heatmap
    vmin, vmax = clim
    # logNorm requires positive values. set it to default None if vmin is zero
    if vmin == 0:
        vmin = None
    image = ax.imshow(data.transpose(), aspect='auto', interpolation='nearest',
                      norm=norm, vmin=vmin, vmax=vmax, cmap=cmap)

    # plot legend of color scale
    legend = fig.colorbar(image, cax=cax)
    # specify tick label font size
    legend.ax.tick_params(labelsize=9)

    # plot x ticks and the white vertical lines between sample groups
    if sample_field is None:
        ax.xaxis.set_visible(False)
    else:
        try:
            ticklabels = exp.sample_metadata[sample_field]
        except KeyError:
            raise ValueError('Sample field %r not in sample metadata' % sample_field)
        _set_axis_ticks(ax, 'x', ticklabels, xticks_max, numcols, xticklabel_kwargs, xticklabel_len)
        ax.set_xlabel(sample_field)

    # plot y tick labels dynamically
    if feature_field is None:
        ax.yaxis.set_visible(False)
    else:
        try:
            ticklabels = exp.feature_metadata[feature_field]
        except KeyError:
            raise ValueError('Feature field %r not in feature metadata' % feature_field)
        _set_axis_ticks(ax, 'y', ticklabels, yticks_max, numrows, yticklabel_kwargs, yticklabel_len)
        ax.set_ylabel(feature_field)

    # set the mouse hover string to the value of abundance (in normal scale)
    def format_coord(x, y):
        row = int(x + 0.5)
        col = int(y + 0.5)
        if 0 <= col < numcols and 0 <= row < numrows:
            z = exp.data[row, col]
            return 'x=%1.2f, y=%1.2f, z=%1.2f' % (x, y, z)
        else:
            return 'x=%1.2f, y=%1.2f' % (x, y)
    ax.format_coord = format_coord

    return ax


def _ax_bars(ax, valuess, colorss=None, widths=0.3, spaces=0.05, labels=True, labels_kwargs=None, axis=0):
    position = 0
    for values, colors, width, space, label, label_kwargs in zip(
            valuess,
            itertools.cycle(_to_list(colorss)),
            itertools.cycle(_to_list(widths)),
            itertools.cycle(_to_list(spaces)),
            itertools.cycle(_to_list(labels)),
            itertools.cycle(_to_list(labels_kwargs))):
        _ax_bar(ax, values, colors, width, position, label, label_kwargs, axis=axis)
        position += (width + space)
    return ax


def _ax_bar(ax, values, colors=None, width=0.3, position=0, label=True, label_kwargs=None, axis=0):
    '''Plot color bars along x or y axis

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        the axes to plot the color bars in.
    values : Iterable
        the values informing the colors on the bar
    width : float
        the width of the color bar
    position : float, optional
        the position of the color bar (its left bottom corner)
    colors : dict, optional
        the colors for each unique value in the ``values`` list.
        if it is ``None``, it will use ``Dark2`` discrete color map
        in a cycling way.
    label : bool, optional
        whether to label the color bars with text
    label_kwargs: dict
        keyword arguments to pass in for :func:`matplotlib.axes.Axes.annotate`

    Returns
    -------
    :class:`matplotlib.axes.Axes`
    '''
    if label_kwargs is None:
        label_kwargs = {}
    kwargs = {'color': 'w', 'weight': 'bold', 'size': 6,
              'ha': 'center', 'va': 'center'}
    kwargs.update(label_kwargs)

    # convert to string and leave it as empty if it is None
    values = ['' if i in {None, np.nan} else str(i) for i in values]
    uniques = np.unique(values)
    if colors is None:
        cmap = mpl.cm.get_cmap('Dark2')
        colors = cmap.colors
        col = dict(zip(uniques, itertools.cycle(colors)))
    else:
        col = colors

    prev = 0
    offset = 0.5
    for i, value in _transition_index(values):
        if value != '':
            # do not plot the current segment of the bar
            # if the value is empty
            if axis == 0:
                # plot the color bar along x axis
                pos = prev - offset, position
                w, h = i - prev, width
                rotation = 0
            else:
                # plot the color bar along y axis
                pos = position, prev - offset
                w, h = width, i - prev
                rotation = 90
            rect = mpatches.Rectangle(
                pos,               # position
                w,                 # width (size along x axis)
                h,                 # height (size along y axis)
                edgecolor="none",  # No border
                facecolor=col[value],
                label=value)
            ax.add_patch(rect)
            if label is True:
                rx, ry = rect.get_xy()
                cx = rx + rect.get_width() / 2.0
                cy = ry + rect.get_height() / 2.0

                # add the text in the color bars
                ax.annotate(value, (cx, cy), rotation=rotation,
                            **kwargs)

        prev = i

    return ax


def plot(exp: Experiment, title=None,
         barx_fields=None, barx_width=0.3, barx_colors=None, barx_label=True, barx_label_kwargs=None,
         bary_fields=None, bary_width=0.3, bary_colors=None, bary_label=True, bary_label_kwargs=None,
         tree=None, tree_size=8, gui='cli', databases=False, **heatmap_kwargs):

    '''Plot the interactive heatmap and its associated axes.

    The heatmap is interactive and can be dynamically updated with
    following key and mouse events:

    +---------------------------+-----------------------------------+
    |Event                      |Description                        |
    +===========================+===================================+
    |`+` or `⇧ →`               |zoom in on x axis                  |
    |                           |                                   |
    +---------------------------+-----------------------------------+
    |`_` or `⇧ ←`               |zoom out on x axis                 |
    |                           |                                   |
    +---------------------------+-----------------------------------+
    |`=` or `⇧ ↑`               |zoom in on y axis                  |
    |                           |                                   |
    +---------------------------+-----------------------------------+
    |`-` or `⇧ ↓`               |zoom out on y axis                 |
    |                           |                                   |
    +---------------------------+-----------------------------------+
    |`left mouse click`         |select the current row and column  |
    +---------------------------+-----------------------------------+
    |`⇧` and `left mouse click` |select all the rows between        |
    |                           |previous selected and current rows |
    +---------------------------+-----------------------------------+
    |`.`                        |move the selection down by one row |
    +---------------------------+-----------------------------------+
    |`,`                        |move the selection up by one row   |
    +---------------------------+-----------------------------------+
    |`<`                        |move the selection left by one     |
    |                           |column                             |
    +---------------------------+-----------------------------------+
    |`>`                        |move the selection right by one    |
    |                           |column                             |
    +---------------------------+-----------------------------------+
    |`↑` or `=`                 |scroll the heatmap up on y axis    |
    +---------------------------+-----------------------------------+
    |`↓` or `-`                 |scroll the heatmap down on y axis  |
    +---------------------------+-----------------------------------+
    |`←` or `<`                 |scroll the heatmap left on x axis  |
    +---------------------------+-----------------------------------+
    |`→` or `>`                 |scroll the heatmap right on x axis |
    +---------------------------+-----------------------------------+


    Parameters
    ----------
    title : str (optional)
        The title of the figure.
    barx_fields, bary_fields : str or list of str, optional
        column name(s) in sample metadata (barx) / feature metadata (bary). It plots a bar
        for each column. It doesn't plot color bars by default (``None``)
    barx_width, bary_width : float, optional
        The width of the bars
    barx_colors, bary_colors : dict, :class:`matplotlib.colors.ListedColormap`, optional
        The colors for each unique values in the column of sample/feature metadata
    barx_label, bary_label : bool, optional
        whether to show the labels on the bars.
    barx_label_kwargs, bary_label_kwargs : dict, optional
        keyword arguments passing to :meth:`matplotlib.axes.Axes.annotate` for labels on the bars
    tree : skbio.TreeNode or None (optional)
        None (default) to not plot a tree
        otherwise, plot the tree dendrogram on the left.
        NOTE: features are reordered according to the tree
    tree_size : int (optional)
        The width of the tree relative to the main heatmap (12 is identical size)
    gui : str, optional
        GUI to use. Choice includes 'cli', 'jupyter', or 'qt5'
    databases : list of str or ``None``
        a list of databases to access or add annotation
        ``None`` (default) to use the default field based on the experiment.
    heatmap_kwargs : dict, optional
        keyword arguments passing to :func:`heatmap` function.

    Returns
    -------
    ``PlottingGUI``
        This object contains the figure of the plot (including all the subplots) as its ``.figure`` attribute

    '''
    # set the databases if default requested (i.e. False)
    if databases is False:
        databases = exp.heatmap_databases

    if tree is None:
        gui_obj = _create_plot_gui(exp, gui, databases)
    else:
        gui_obj = _create_plot_gui(exp, gui, databases, tree_size=tree_size)
        # match the exp order to the tree (reorders the features)
        exp, tree = plot_tree(exp, tree, gui_obj.ax_tre)

    if title is not None:
        gui_obj.figure.suptitle(title)

    exp.heatmap(ax=gui_obj.ax_hm, cax=gui_obj.ax_legend, **heatmap_kwargs)

    if barx_fields is not None:
        _ax_bars(gui_obj.ax_sbar,
                 valuess=(exp.sample_metadata[column] for column in _to_list(barx_fields)),
                 colorss=barx_colors,
                 widths=barx_width,
                 labels=barx_label,
                 labels_kwargs=barx_label_kwargs,
                 axis=0)

    if bary_fields is not None:
        _ax_bars(gui_obj.ax_fbar,
                 valuess=(exp.feature_metadata[column] for column in _to_list(bary_fields)),
                 colorss=bary_colors,
                 widths=bary_width,
                 labels=bary_label,
                 labels_kwargs=bary_label_kwargs,
                 axis=1)

    # set up the gui ready for interaction
    gui_obj()

    return gui_obj
