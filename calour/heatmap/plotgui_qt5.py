import sys
from logging import getLogger
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QHBoxLayout, QVBoxLayout,
                             QSizePolicy, QWidget, QPushButton,
                             QLabel, QListWidget, QSplitter, QFrame,
                             QComboBox, QScrollArea, QListWidgetItem,
                             QDialogButtonBox, QApplication)
from PyQt5.QtCore import Qt

from .plotgui import PlotGUI
from .. import analysis


logger = getLogger(__name__)


class PlotGUI_QT5(PlotGUI):
    '''QT5 version of plot winfow GUI

    We open the figure as a widget inside the qt5 window

    Attributes
    ----------
    figure : ``matplotlib.figure.Figure``
    app : QT5 App created
    app_window : Windows belonging to the QT5 App
    databases :
    '''
    def __init__(self, *kargs, **kwargs):
        super().__init__(*kargs, **kwargs)
        # create qt app
        app = QtCore.QCoreApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            logger.debug('Qt app created')
        self.app = app
        if not hasattr(app, 'references'):
            # store references to all the windows
            app.references = set()
        # create app window
        self.app_window = ApplicationWindow(self)
        app.references.add(self.app_window)
        self.app_window.setWindowTitle("Calour")
        self._set_figure(self.app_window.plotfigure)

    def __call__(self):
        logger.debug('opening Qt5 window')
        super().__call__()
        try:
            self.app_window.show()
            # move the window to the front
            self.app_window.activateWindow()
            self.app_window.raise_()
            # run the event loop
            self.app.exec_()
        finally:
            # clean up when the qt app is closed
            if self.app_window in self.app.references:
                logger.debug('removing window from app window list')
                self.app.references.remove(self.app_window)
            else:
                logger.debug('window not in app window list. Not removed')

    def show_info(self):
        sid, fid, abd, annt = self.get_info()
        self._update_info_labels(sid, fid, abd)
        self._display_annotation_in_qlistwidget(annt)

    def _update_info_labels(self, sid, fid, abd):
        self.app_window.w_abund.setText('{:.01f}'.format(abd))
        self.app_window.w_fid.setText(fid)
        self.app_window.w_sid.setText(sid)
        sample_field = str(self.app_window.w_sfield.currentText())
        self.app_window.w_sfield_val.setText(
            str(self.exp.sample_metadata[sample_field][self.current_select[0]]))
        feature_field = str(self.app_window.w_ffield.currentText())
        self.app_window.w_ffield_val.setText(
            str(self.exp.feature_metadata[feature_field][self.current_select[1]]))

    def _display_annotation_in_qlistwidget(self, annt):
        '''Add a line to the annotation list

        It does not erase previous lines.

        Parameters
        ----------
        annt : list of (dict, str)
            dict : contains the key 'annotationtype' and determines the annotation color
            also contains all other annotation data needed for right click menu/double click
            str : The string to add to the list
        '''
        # clear the previous annotation box
        self.app_window.w_dblist.clear()

        for cannt in annt:
            details = cannt[0]
            newitem = QListWidgetItem(cannt[1])
            newitem.setData(QtCore.Qt.UserRole, details)
            if details['annotationtype'] == 'diffexp':
                ccolor = QtGui.QColor(0, 0, 200)
            elif details['annotationtype'] == 'contamination':
                ccolor = QtGui.QColor(200, 0, 0)
            elif details['annotationtype'] == 'common':
                ccolor = QtGui.QColor(0, 200, 0)
            elif details['annotationtype'] == 'highfreq':
                ccolor = QtGui.QColor(0, 200, 0)
            else:
                ccolor = QtGui.QColor(0, 0, 0)
            newitem.setForeground(ccolor)
            self.app_window.w_dblist.addItem(newitem)


class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.).

    Parameters
    ----------
    parent :
    width, height : Numeric
        size of the canvas
    dpi : int

    """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        # comment out because it draws frame on the whole plotting area
        # self.axes = fig.add_subplot(111)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class ApplicationWindow(QMainWindow):
    def __init__(self, gui):
        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.main_widget = QWidget(self)

        scroll_box_width = 800
        # set the GUI widgets
        # the user side on the right
        userside = QVBoxLayout()
        # sample field to display
        lbox = QHBoxLayout()
        self.w_sfield = QComboBox()
        self.w_sfield_val = QLabel(text='NA')
        self.w_sfield_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        scroll = QScrollArea()
        scroll.setFixedHeight(18)
        self.w_sfield_val.setMinimumWidth(scroll_box_width)
        scroll.setWidget(self.w_sfield_val)
        lbox.addWidget(self.w_sfield)
        lbox.addWidget(scroll)
        userside.addLayout(lbox)
        # add the sample field combobox values
        for i in gui.exp.sample_metadata.columns:
            self.w_sfield.addItem(str(i))
        # feature field to display
        lbox = QHBoxLayout()
        self.w_ffield = QComboBox()
        self.w_ffield_val = QLabel(text='NA')
        self.w_ffield_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        scroll = QScrollArea()
        scroll.setFixedHeight(18)
        self.w_ffield_val.setMinimumWidth(scroll_box_width)
        scroll.setWidget(self.w_ffield_val)
        lbox.addWidget(self.w_ffield)
        lbox.addWidget(scroll)
        userside.addLayout(lbox)
        for i in gui.exp.feature_metadata.columns:
            self.w_ffield.addItem(str(i))

        # sample id
        lbox = QHBoxLayout()
        label = QLabel(text='Sample ID:')
        scroll = QScrollArea()
        scroll.setFixedHeight(18)
        self.w_sid = QLabel(text='?')
        self.w_sid.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.w_sid.setMinimumWidth(scroll_box_width)
        scroll.setWidget(self.w_sid)
        lbox.addWidget(label)
        lbox.addWidget(scroll)
        userside.addLayout(lbox)
        # feature id
        lbox = QHBoxLayout()
        label = QLabel(text='Feature ID:')
        scroll = QScrollArea()
        scroll.setFixedHeight(18)
        self.w_fid = QLabel(text='?')
        self.w_fid.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.w_fid.setMinimumWidth(scroll_box_width)
        scroll.setWidget(self.w_fid)
        lbox.addWidget(label)
        lbox.addWidget(scroll)
        userside.addLayout(lbox)
        # abundance value
        lbox = QHBoxLayout()
        label = QLabel(text='Abundance:')
        self.w_abund = QLabel(text='?')
        lbox.addWidget(label)
        lbox.addWidget(self.w_abund)
        userside.addLayout(lbox)
        # buttons
        lbox_buttons = QHBoxLayout()
        self.w_sequence = QPushButton(text='Copy Seq')
        lbox_buttons.addWidget(self.w_sequence)
        self.w_info = QPushButton(text='Info')
        lbox_buttons.addWidget(self.w_info)
        self.w_annotate = QPushButton(text='Annotate')
        lbox_buttons.addWidget(self.w_annotate)
        userside.addLayout(lbox_buttons)
        # db annotations list
        self.w_dblist = QListWidget()
        self.w_dblist.itemDoubleClicked.connect(self.double_click_annotation)
        userside.addWidget(self.w_dblist)
        # the annotation list right mouse menu
        self.w_dblist.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.w_dblist.customContextMenuRequested.connect(self.annotation_list_right_clicked)
        # buttons at bottom
        lbox_buttons_bottom = QHBoxLayout()
        self.w_save_fasta = QPushButton(text='Save Seqs')
        lbox_buttons_bottom.addWidget(self.w_save_fasta)
        self.w_enrichment = QPushButton(text='Enrichment')
        lbox_buttons_bottom.addWidget(self.w_enrichment)
        userside.addLayout(lbox_buttons_bottom)

        # the heatmap on the left side
        heatmap = MplCanvas(self.main_widget, width=5, height=4, dpi=100)
        heatmap.setFocusPolicy(QtCore.Qt.ClickFocus)
        heatmap.setFocus()

        layout = QHBoxLayout(self.main_widget)
        frame = QFrame()
        splitter = QSplitter(QtCore.Qt.Horizontal, self.main_widget)
        splitter.addWidget(heatmap)
        frame.setLayout(userside)
        splitter.addWidget(frame)
        layout.addWidget(splitter)

        self.plotfigure = heatmap.figure
        self.gui = gui

        # link events to gui
        self.w_annotate.clicked.connect(self.annotate)
        self.w_sequence.clicked.connect(self.copy_sequence)
        self.w_save_fasta.clicked.connect(self.save_fasta)
        self.w_enrichment.clicked.connect(self.enrichment)
        self.w_sfield.currentIndexChanged.connect(self.info_field_changed)
        self.w_ffield.currentIndexChanged.connect(self.info_field_changed)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def annotation_list_right_clicked(self, QPos):
        self.listMenu = QtWidgets.QMenu()
        parent_position = self.w_dblist.mapToGlobal(QtCore.QPoint(0, 0))
        item = self.w_dblist.itemAt(QPos)
        data = item.data(QtCore.Qt.UserRole)
        db = data.get('_db_interface', None)
        if db is None:
            logger.debug('No database for selected item')
            return
        menu_details = self.listMenu.addAction("Details")
        menu_details.triggered.connect(lambda: self.right_menu_details(item))
        if db.annotatable:
            menu_details = self.listMenu.addAction("Update annotation")
            menu_details.triggered.connect(lambda: self.right_menu_update(item))
            menu_delete = self.listMenu.addAction("Delete annotation")
            menu_delete.triggered.connect(lambda: self.right_menu_delete(item))
            menu_remove = self.listMenu.addAction("Remove seq. from annotation")
            menu_remove.triggered.connect(lambda: self.right_menu_remove_feature(item))
        self.listMenu.move(parent_position + QPos)
        self.listMenu.show()

    def right_menu_details(self, item):
        self.double_click_annotation(item)

    def right_menu_delete(self, item):
        if QtWidgets.QMessageBox.warning(self, "Delete annotation?", "Are you sure you want to delete the annotation:\n%s\n"
                                         "and all associated features?" % item.text(),
                                         QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.No:
            return
        data = item.data(QtCore.Qt.UserRole)
        db = data.get('_db_interface', None)
        logger.debug('Deleting annotation %s' % item.text())
        err = db.delete_annotation(data)
        if err:
            logger.error('Annotation not deleted. Error: %s' % err)
        self.gui.show_info()

    def right_menu_update(self, item):
        logger.debug('update annotation %s' % item.text)
        data = item.data(QtCore.Qt.UserRole)
        db = data.get('_db_interface', None)
        db.upadte_annotation(data, self.gui.exp)

    def right_menu_remove_feature(self, item):
        features = self.gui.get_selected_seqs()
        if QtWidgets.QMessageBox.warning(self, "Remove feature from annotation?", "Are you sure you want to remove the %d selected features\n"
                                         "from the annotation:\n%s?" % (len(features), item.text()), QtWidgets.QMessageBox.Yes,
                                         QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.No:
            return
        data = item.data(QtCore.Qt.UserRole)
        db = data.get('_db_interface', None)
        logger.debug('Removing %d features from annotation %s' % (features, item.text()))
        err = db.remove_features_from_annotation(features, data)
        if err:
            logger.error('Features not removed from annotation. Error: %s' % err)

    def info_field_changed(self):
        sid, fid, abd = self.gui.get_selection_info()
        self.gui._update_info_labels(sid, fid, abd)

    def copy_sequence(self):
        '''Copy the sequence to the clipboard
        '''
        cseq = self.gui.exp.feature_metadata.index[self.gui.current_select[1]]
        clipboard = QApplication.clipboard()
        clipboard.setText(cseq)

    def save_fasta(self):
        seqs = self.gui.get_selected_seqs()
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, caption='Save selected seqs to fasta')
        self.gui.exp.save_fasta(str(filename), seqs)

    def enrichment(self):
        group1_seqs = self.gui.get_selected_seqs()
        allseqs = self.gui.exp.feature_metadata.index.values
        group2_seqs = list(set(allseqs).difference(set(group1_seqs)))

        logger.debug('Getting experiment annotations for %d features' % len(allseqs))
        for cdb in self.gui.databases:
            if not cdb.can_get_feature_terms:
                continue
            logger.debug('Database: %s' % cdb.get_name())
            feature_terms = cdb.get_feature_terms(allseqs, self.gui.exp)
            logger.debug('got %d terms' % len(feature_terms))
            res = analysis.relative_enrichment(self.gui.exp, group1_seqs, feature_terms)
            logger.debug('Got %d enriched terms' % len(res))
            if len(res) == 0:
                QtWidgets.QMessageBox.information(self, "No enriched terms found",
                                                  "No enriched annotations found when comparing\n%d selected sequences to %d "
                                                  "other sequences" % (len(group1_seqs), len(group2_seqs)))
                return
            listwin = SListWindow(listname='enriched ontology terms')
            for cres in res:
                if cres['group1'] > cres['group2']:
                    ccolor = 'blue'
                else:
                    ccolor = 'red'
                cname = cres['description']
                listwin.add_item('%s - %f (selected %f, other %f) ' % (cname, cres['pval'], cres['group1'], cres['group2']), color=ccolor)
            listwin.exec_()

    def double_click_annotation(self, item):
        '''Show database information about the double clicked item in the list.

        Call the appropriate database for displaying the info
        '''
        data = item.data(QtCore.Qt.UserRole)
        db = data.get('_db_interface', None)
        if db is None:
            return
        db.show_annotation_info(data)

    def annotate(self):
        '''Add database annotation to selected features
        '''
        # get the database used to add annotation
        if self.gui._annotation_db is None:
            logger.warn('No database with add annotation capability selected (use plot(...,databases=[dbname])')
            return
        # get the sequences of the selection
        seqs = self.gui.get_selected_seqs()
        # annotate
        err = self.gui._annotation_db.add_annotation(seqs, self.gui.exp)
        if err:
            logger.error('Error encountered when adding annotaion: %s' % err)
            return
        logger.info('Annotation added')


class SListWindow(QtWidgets.QDialog):
    def __init__(self, listdata=[], listname=None):
        '''Create a list window with items in the list and the listname as specified

        Parameters
        ----------
        listdata: list of str (optional)
            the data to show in the list
        listname: str (optional)
            name to display above the list
        '''
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        if listname is not None:
            self.setWindowTitle(listname)

        self.layout = QVBoxLayout(self)

        self.w_list = QListWidget()
        self.layout.addWidget(self.w_list)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)
        self.layout.addWidget(buttonBox)

        for citem in listdata:
            self.w_list.addItem(citem)

        self.show()
        self.adjustSize()

    def add_item(self, text, color='black'):
        '''Add an item to the list

        Parameters
        ----------
        text : str
            the string to add
        color : str (optional)
            the color of the text to add
        '''
        item = QtWidgets.QListWidgetItem()
        item.setText(text)
        if color == 'black':
            ccolor = QtGui.QColor(0, 0, 0)
        elif color == 'red':
            ccolor = QtGui.QColor(155, 0, 0)
        elif color == 'blue':
            ccolor = QtGui.QColor(0, 0, 155)
        elif color == 'green':
            ccolor = QtGui.QColor(0, 155, 0)
        item.setForeground(ccolor)
        self.w_list.addItem(item)
