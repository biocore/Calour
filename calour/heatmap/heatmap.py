# ----------------------------------------------------------------------------
# Copyright (c) 2016--,  Calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from logging import getLogger
import importlib

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


logger = getLogger(__name__)


def _transition_index(l):
    '''Return the transition index and current value of the list.

    Examples
    -------
    >>> l = ['a', 'a', 'b']
    >>> list(_transition_index(l))
    [(0, 'a'), (2, 'b')]

    Parameters
    ----------
    l : list, 1-D array, pd.Series
        l should have method of len and [
    '''
    cur = l[0]
    yield 0, cur
    for i in range(1, len(l)):
        if l[i] != cur:
            yield i, l[i]
            cur = l[i]


def plot(exp, sample_field=None, feature_field=None, max_features=1000,
         logit=True, log_cutoff=1, clim=(0, 10), xlabel_rotation=45, xlabel_maxlen=10, cmap=None, title=None,
         gui='cli', databases=['dbbact'], axis=None, rect=None):
    '''Plot an experiment heatmap

    Plot an interactive heatmap for the experiment

    Parameters
    ----------
    sample_field : str or None (optional)
        The field to display on the x-axis (sample):
        None (default) to not show x labels.
        str to display field values for this field
    feature_field : str or None (optional)
        Name of the field to display on the y-axis (features) or None not to display names
    max_features : int (optional)
        The maximal number of feature names to display in the plot (when zoomed out)
        0 to show all labels
    logit : bool (optional)
        True (default) to calculate mean of the log2 transformed data (useful for reducing outlier effect)
        False to not log transform before mean calculation
    log_cutoff : float (optional)
        The minimal number of reads for the log trasnform (if logit=True)
    clim : tuple of (float, float) or None (optional)
        the min and max values for the heatmap or None to use all range
    xlabel_rotation : float (optional)
        The rotation angle for the x labels (if sample_field is supplied)
    xlabel_rotation : int (optional) or None
        The maximal length for the x label strings (will be cut to this length if longer). Used to prevent long labels from taking too much space.
        None indicates no cutting
    colormap : None or str (optional)
        None (default) to use mpl default color map. str to use colormap named str.
    title : None or str (optional)
        None (default) to show experiment description field as title. str to set title to str.
    gui : str (optional)
        Name of the gui module to use for displaying the heatmap. options:
        'cli' : just cli information about selected sample/feature.
        'qt5' : gui using QT5 (with full dbBact interface)
        'jupyter' : gui for Jupyter notebooks (using widgets)
        Other string : name of child class of plotgui (which should reside in heatmap/lower(classname).py)
    databases : list of str (optional)
        Names of the databases to use to obtain info about sequences. options:
        'dbbact' : the dbBact manual annotation database
        'spongeworld' : the sponge microbiome automatic annotation database
        'redbiom' : the automatic qiita database
    axis : matplotlib axis or None (optional)
        None (default) to create a new figure, axis to plot heatmap into the axis
    rect : list of int or None (optional)
        None (default) to set initial zoom window to all experiment.
        [x_min, x_max, y_min, y_max] to set initial zoom window
    '''
    logger.debug('plot experiment')
    data = exp.get_data(sparse=False)
    if logit:
        # log transform if needed
        logger.debug('log2 transforming cutoff %f' % log_cutoff)
        data[data < log_cutoff] = log_cutoff
        data = np.log2(data)

    # init the default colormap
    if cmap is None:
        cmap = plt.rcParams['image.cmap']

    # load the appropriate gui module to handle gui events
    if gui == 'qt5':
        gui = 'PlotGUI_QT5'
    elif gui == 'cli':
        gui = 'PlotGUI_CLI'
    elif gui == 'jupyter':
        gui = 'PlotGUI_Jupyter'
    else:
        raise ValueError('Unknown GUI specified: %r' % gui)
    gui_module_name = 'calour.heatmap.' + gui.lower()
    gui_module = importlib.import_module(gui_module_name)
    # get the class
    GUIClass = getattr(gui_module, gui)
    hdat = GUIClass(exp)
    hdat._annotation_db = None

    # link with the databases requested
    for cdatabase in databases:
        if cdatabase == 'dbbact':
            db_name = 'DBBact'
            db_module_name = 'dbbact_calour.dbbact'
        elif cdatabase == 'spongeworld':
            db_name = 'DBSponge'
            db_module_name = 'dbbact_calour.dbsponge'
        else:
            raise ValueError('Unknown Database specified: %r' % cdatabase)

        # import the database module
        db_module = importlib.import_module(db_module_name)
        # get the class
        DBClass = getattr(db_module, db_name)
        cdb = DBClass()
        hdat.databases.append(cdb)
        # select the database for use with the annotate button
        if cdb.can_annotate():
            if hdat._annotation_db is None:
                hdat._annotation_db = cdb
            else:
                logger.warn('More than one database with annotation capability. Using first database (%s) for annotation' % hdat._annotation_db.get_name())

    # init the figure
    if axis is None:
        fig = hdat.get_figure()
        ax = fig.gca()
    else:
        fig = axis.get_figure()
        ax = axis

    hdat.axis = ax
    hdat.fig = fig

    # plot the heatmap
    image = ax.imshow(data.transpose(), aspect='auto', interpolation='nearest', cmap=cmap, clim=clim)

    # set the initial zoom window if supplied
    if rect is not None:
        ax.set_xlim((rect[0], rect[1]))
        ax.set_ylim((rect[2], rect[3]))

    # plot vertical lines between sample groups and add x labels for the field
    if sample_field is not None:
        x_pos, x_val = zip(*[(pos, val) for pos, val in _transition_index(
            exp.sample_metadata[sample_field])])
        # samples start - 0.5 before and go to 0.5 after
        for pos in x_pos[1:]:
            ax.axvline(x=pos - 0.5, color='white')
        x_pos = list(x_pos)
        x_pos.append(exp.data.shape[0])
        x_pos = np.array(x_pos)
        ax.set_xticks(x_pos[:-1] + (x_pos[1:] - x_pos[:-1]) / 2)
        # shorten xlabels that are too long:
        if xlabel_maxlen is not None:
            x_val = [str(clabel[:2]) + '..' + str(clabel[5-xlabel_maxlen:]) if len(str(clabel)) > xlabel_maxlen else str(clabel) for clabel in x_val]
        ax.set_xticklabels(x_val, rotation=xlabel_rotation, ha='right')

    # plot y ticks and labels
    if feature_field is not None:
        if feature_field not in exp.feature_metadata:
            raise ValueError('Feature field %s not in feature metadata' % feature_field)
        labels = [x for x in exp.feature_metadata[feature_field]]
        ylabel_maxlen = 15
        labels = [clabel[-ylabel_maxlen:] if len(clabel) > ylabel_maxlen else clabel for clabel in labels]
        xs = np.arange(len(labels))

        # display only when zoomed enough
        def format_fn(tick_val, tick_pos):
            if int(tick_val) in xs:
                return labels[int(tick_val)]
            else:
                return ''
        if max_features > 0:
            # set the maximal number of feature lables
            ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(format_fn))
            ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(max_features, integer=True))
            ax.tick_params(axis='y', labelsize=8)
        else:
            # otherwise show all labels
            ax.set_yticks(xs, fontsize=8)

    # set the mouse hover string to the value of abundance
    def x_y_info(x, y):
        z = image.get_array()[int(y), int(x)]
        if logit:
            z = np.power(2, z)
        return '{0:.01f}'.format(z)
    ax.format_coord = x_y_info

    # set the title
    if title is None:
        title = exp.description
    ax.set_title(title)

    # link the interactive plot functions
    hdat.connect_functions(fig)

    # make the axis titles show
    fig.tight_layout()
    plt.show()
    hdat.run_gui()
