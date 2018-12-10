#!/usr/bin/env python3

import sys
import os
import subprocess
import logging
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtCore import QFileSystemWatcher
from model import Model

LogViewerWindow = "./Design/LogViewer_test.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(LogViewerWindow)

# -----------------------------------------------------------------------------


class LogViewer(QtWidgets.QMainWindow, Ui_MainWindow):
    # -----------------------------------------------------------------------------
    def __init__(self, argv):
        logging.basicConfig(filename='trace.log', level=logging.DEBUG)

        self.changeDetection = False

        self.app = QtWidgets.QApplication(argv)
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.model = Model()

        self.setupUi(self)

        self.PB_SearchDir.clicked.connect(self.on_PB_SearchDir)

        self.treeViewDirectory.clicked.connect(self.on_treeViewDirectoryClicked)
        self.treeViewDirectory.doubleClicked.connect(self.on_treeViewDirectoryDoubleClicked)


        self.QuitPb.clicked.connect(self.on_quit)


    # -----------------------------------------------------------------------------

    def on_PB_SearchDir( self ):
        ''' Called when the user presses the Browse button
        '''
        logging.debug( "Browse button pressed" )
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        directoryName = QtWidgets.QFileDialog.getExistingDirectory(
                        None,
                        "Select Output Folder",
                        "",
                        options=options)
        if directoryName:
            logging.debug( "setting directory name: " + directoryName )
            self.model.setDirectoryName( directoryName )
            self.refreshDir()
            self.treeViewDirectory.selectionModel().currentChanged.connect(self.on_treeViewDirectoryClicked)

            if self.changeDetection == True:
                self._pathToWatch = directoryName
                self._fileSysWatcher = QFileSystemWatcher()
                self._initialContent = os.listdir(self._pathToWatch)
                for f in self._initialContent:
                    if (f != "trace.log"):
                        self._fileSysWatcher.addPath(f)

                self._fileSysWatcher.fileChanged.connect(self.slotDirChanged)
                self._fileSysWatcher.directoryChanged.connect(self.slotDirChanged)

    def slotDirChanged(self, path):
        logging.debug("Detected Change!!" + path)

    def on_treeViewDirectoryClicked(self, index):
        path = self.sender().model().filePath(index)
        logging.debug("on_treeViewDirectoryClicked on: " + path)
        self.model.setFileName(path)
        self.refreshAll()

    def on_treeViewDirectoryDoubleClicked(self, index):
        path = self.sender().model().filePath(index)
        logging.debug("on_treeViewDirectoryDoubleClicked on: " + path)
        subprocess.Popen(["uex", path])

    def on_directoryChanged(self, index):
        path = self.sender().model().filePath(index)
        logging.debug("on_fileChanged on: " + path)

    # -----------------------------------------------------------------------------
    def refreshDir(self):
        directory = self.model.getDirectoryName()
        self.lineEdit_SearchDir.setText(directory)
        fileSystemModel = QFileSystemModel()
        fileSystemModel.setRootPath('')

        self.treeViewDirectory.setModel(fileSystemModel)
        self.treeViewDirectory.setRootIndex(fileSystemModel.index(directory))

        self.treeViewDirectory.setAnimated(False)
        self.treeViewDirectory.setIndentation(20)
        self.treeViewDirectory.setSortingEnabled(True)

        self.treeViewDirectory.setWindowTitle("Dir View")

    # -----------------------------------------------------------------------------
    def refreshAll( self ):
        '''
        Updates the widgets whenever an interaction happens.
        Typically some interaction takes place, the UI responds,
        and informs the model of the change.  Then this method
        is called, pulling from the model information that is
        updated in the GUI.
        '''

        self.lineEdit_SearchDir.setText(self.model.getDirectoryName())

        self.lineEdit.setText( self.model.getFileName() )
        self.textEdit.setText( self.model.getFileContents() )

    # -----------------------------------------------------------------------------
    def on_quit(self):
            self.app.quit()

    # -----------------------------------------------------------------------------
    def start_gui(self):
        self.show()
        self.app.exec_()

# -----------------------------------------------------------------------------


def main():
    log_viewer_starter = LogViewer(sys.argv)

    log_viewer_starter.start_gui()


if __name__ == "__main__":
    main()
