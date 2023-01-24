'''
Created on May 20, 2015

@author: hsorby
'''
import os
import re
import pydicom

from PySide6 import QtWidgets

from mapclientplugins.dicomheaderquerystep.view.ui_dicomheaderwidget import Ui_DicomHeaderWidget


def tryint(s):
    try:
        return int(s)
    except:
        return s


def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
    "z23a" -> ["z", 23, "a"]
    """
    return [tryint(c) for c in re.split('([0-9]+)', s)]


class DICOMHeaderWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(DICOMHeaderWidget, self).__init__(parent)
        self._ui = Ui_DicomHeaderWidget()
        self._ui.setupUi(self)
        horz_header = self._ui.tableWidgetSavedQueries.horizontalHeader()
        cols = self._ui.tableWidgetSavedQueries.columnCount()
        for col in range(cols):
            horz_header.setResizeMode(col, QtWidgets.QHeaderView.Stretch)
        self._image_data = None
        self._makeConnections()
        self._active_ds = None
        self._active_combo_box = None

    def _makeConnections(self):
        self._ui.pushButtonQuery.clicked.connect(self._queryButtonClicked)
        self._ui.comboBoxDICOMImage.currentIndexChanged.connect(self._DICOMImageChanged)
        self._ui.comboBoxDICOMKeyword.currentIndexChanged.connect(self._DICOMQueryChanged)
        self._ui.comboBoxDICOMTag.currentIndexChanged.connect(self._DICOMQueryChanged)
        self._ui.pushButtonStore.clicked.connect(self._storeButtonClicked)
        self._ui.pushButtonRemove.clicked.connect(self._removeButtonClicked)
        selection_model = self._ui.tableWidgetSavedQueries.selectionModel()
        selection_model.selectionChanged.connect(self._saveQueriesSelectionChanged)

    def _DICOMQueryChanged(self):
        self._active_combo_box = self.sender()

    def _queryButtonClicked(self):
        if self._active_ds:
            text = str(self._active_combo_box.currentText())
            if text.startswith('('):
                # Assume we have a tag
                code_1, code_2 = text.split(',')
                data_element = self._active_ds[code_1[1:], code_2[:-1]]
            else:
                data_element = self._active_ds.data_element(text)

            # Set all settings
            self._ui.labelHiddenImage.setText(self._ui.comboBoxDICOMImage.currentText())
            if self._active_combo_box == self._ui.comboBoxDICOMKeyword:
                self._ui.labelHiddenKeyword.setText(self._active_combo_box.currentText())
                self._ui.labelHiddenTag.setText(str(data_element.tag))
            elif self._active_combo_box == self._ui.comboBoxDICOMTag:
                self._ui.labelHiddenTag.setText(self._active_combo_box.currentText())
                # Don't appear to have a map from Tag to Keyword
                self._ui.labelHiddenKeyword.setText('')
            self._ui.lineEditElementName.setText(data_element.name)
            self._ui.lineEditElementRepresentation.setText(data_element.VR)
            self._ui.lineEditElementMultiplicity.setText(str(data_element.VM))
            self._ui.lineEditElementValue.setText(str(data_element.value))

    def _storeButtonClicked(self):
        image = self._ui.labelHiddenImage.text()
        tag = self._ui.labelHiddenTag.text()
        keyword = self._ui.labelHiddenKeyword.text()
        name = self._ui.lineEditElementName.text()
        representation = self._ui.lineEditElementRepresentation.text()
        value = self._ui.lineEditElementValue.text()
        mult = self._ui.lineEditElementMultiplicity.text()
        if image and tag and name:
            self._addTableRow(image, tag, keyword, name, representation, value, mult)

    def _removeButtonClicked(self):
        selected_items = self._ui.tableWidgetSavedQueries.selectedItems()
        item = selected_items[0]
        self._ui.tableWidgetSavedQueries.removeRow(item.row())

    def _saveQueriesSelectionChanged(self):
        selected_items = self._ui.tableWidgetSavedQueries.selectedItems()
        if selected_items:
            self._ui.pushButtonRemove.setEnabled(True)
        else:
            self._ui.pushButtonRemove.setEnabled(False)

    def _DICOMImageChanged(self):
        dicom_image = os.path.join(self._image_data.location(), self._ui.comboBoxDICOMImage.currentText())
        self._active_ds = pydicom.read_file(dicom_image)

        self._ui.comboBoxDICOMTag.blockSignals(True)
        self._ui.comboBoxDICOMTag.clear()
        self._ui.comboBoxDICOMTag.blockSignals(False)
        self._ui.comboBoxDICOMTag.addItems([str(key) for key in self._active_ds.keys()])

        self._ui.comboBoxDICOMKeyword.blockSignals(True)
        self._ui.comboBoxDICOMKeyword.clear()
        self._ui.comboBoxDICOMKeyword.blockSignals(False)
        self._ui.comboBoxDICOMKeyword.addItems(self._active_ds.dir())

        self._active_combo_box = self._ui.comboBoxDICOMTag

    def _addTableRow(self, image, tag, keyword, name, representation, value, mult):
        data = [image, tag, keyword, name, representation, value, mult]
        row = self._ui.tableWidgetSavedQueries.rowCount()
        self._ui.tableWidgetSavedQueries.insertRow(row)
        for col, data_item in enumerate(data):
            item = QtWidgets.QTableWidgetItem(data_item)
            self._ui.tableWidgetSavedQueries.setItem(row, col, item)

    def registerDoneExecution(self, callback):
        self._ui.pushButtonDone.clicked.connect(callback)

    def setImageData(self, image_data):
        self._ui.comboBoxDICOMImage.blockSignals(True)
        self._ui.comboBoxDICOMImage.clear()
        self._ui.comboBoxDICOMImage.blockSignals(False)

        self._image_data = image_data
        # Get list of images?
        directory = image_data.location()
        files = os.listdir(directory)
        files.sort(key=alphanum_key)
        files = [image_file for image_file in files if image_file not in ['.hg', '.git', 'annotation.rdf']]
        self._ui.comboBoxDICOMImage.addItems(files)

    def getStoredQueries(self):
        queries = {}
        rows = self._ui.tableWidgetSavedQueries.rowCount()
        cols = self._ui.tableWidgetSavedQueries.columnCount()
        for row in range(rows):
            image = None
            for col in range(cols):
                header_item = self._ui.tableWidgetSavedQueries.horizontalHeaderItem(col)
                item = self._ui.tableWidgetSavedQueries.item(row, col)
                if col == 0:
                    image = item.text()
                    if image in queries:
                        queries[image].append({header_item.text(): image})
                    else:
                        queries[image] = [{header_item.text(): image}]
                else:
                    queries[image][-1][header_item.text()] = item.text()

        return queries
