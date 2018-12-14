#!/usr/bin/env python3

import sys
import os
import subprocess
import logging
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtCore import QFileSystemWatcher, Qt
from model import Model
from lxml import etree

LogViewerWindow = "./Design/LogViewer.ui"
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

        self.lineEdit_XSD.setText("./xml/xsd/sentinel.xsd")
        self.pb_SearchDir.clicked.connect(self.on_pb_SearchDir)

        self.treeViewDirectory.clicked.connect(self.on_treeViewDirectoryClicked)
        self.treeViewDirectory.doubleClicked.connect(self.on_treeViewDirectoryDoubleClicked)

        self.pb_reload.clicked.connect(self.on_pb_reloadClicked)
        self.pb_valid.clicked.connect(self.on_pb_validClicked)

        self.checkBox_syntaxHightlighting.clicked.connect(self.on_checkBox_syntaxHightlighting)
        self.lineEdit_goto.setValidator(QtGui.QIntValidator(0,2147483647));
        self.pushButton_goto.clicked.connect(self.scrollToLine)

        self.actionExit.triggered.connect(self.on_quit)


    # -----------------------------------------------------------------------------

    def on_pb_SearchDir( self ):
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

            if self.changeDetection == True:
                self._pathToWatch = directoryName
                self._fileSysWatcher = QFileSystemWatcher()
                self._initialContent = os.listdir(self._pathToWatch)
                for f in self._initialContent:
                    if (f != "trace.log"):
                        self._fileSysWatcher.addPath(f)

                self._fileSysWatcher.fileChanged.connect(self.slotDirChanged)
                self._fileSysWatcher.directoryChanged.connect(self.slotDirChanged)

    def on_pb_reloadClicked(self):
        self.refreshDir()

    def on_pb_validClicked(self):
        self.validateXML2(self.model.getFileName(), self.lineEdit_XSD.text())

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
        if os.path.isfile(path):
            subprocess.Popen(["uex", path])

    def on_checkBox_syntaxHightlighting(self):
        if self.checkBox_syntaxHightlighting.isChecked():
            self.highlighter = Highlighter(self.textEdit.document())
        else:
            self.highlighter = None

        if (self.model.getFileName() != None):
            self.refreshAll()

    def scrollToLine(self):
        if (self.lineEdit_goto.text() != ''):
            cursor = QtGui.QTextCursor(self.textEdit.document().findBlockByLineNumber(int(self.lineEdit_goto.text())-1))
            format = QtGui.QTextBlockFormat()
            format.setBackground(Qt.yellow)
            cursor.setBlockFormat(format)
            self.textEdit.moveCursor(QtGui.QTextCursor.End)
            self.textEdit.setTextCursor(cursor)


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
        self.treeViewDirectory.sortByColumn(0, Qt.AscendingOrder)

        self.treeViewDirectory.setWindowTitle("Dir View")
        self.treeViewDirectory.selectionModel().currentChanged.connect(self.on_treeViewDirectoryClicked)

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
    def validateXML2(self, xml_path: str, xsd_path: str):
        if (xml_path == None):
            self.textEdit_XSD.setText("No file selected")
            return
        if (xsd_path == None):
            self.textEdit_XSD.setText("No xsd selected")
            return

        try:
            with open(xsd_path, 'rb') as f:
                schema_root = etree.XML(f.read())

            schema = etree.XMLSchema(schema_root)
            xmlparser = etree.XMLParser(schema=schema)

            with open(xml_path, 'rb') as f:
                etree.fromstring(f.read(), xmlparser)
        except etree.XMLSyntaxError as e:
            logging.debug(e)
            for error in e.error_log:
                self.textEdit_XSD.setText("ERROR ON LINE %s: %s" % (error.line, error.message.encode("utf-8")))
            return False
        except etree.DocumentInvalid as e:
            logging.debug(e)
            for error in e.error_log:
                self.textEdit_XSD.setText("ERROR ON DOCUMENT ERROR LINE %s: %s" % (error.line, error.message.encode("utf-8")))
            return False
        except etree.XMLSchemaParseError as e:
            logging.debug(e)
            for error in e.error_log:
                self.textEdit_XSD.setText("ERROR ON PARSING FILE AT LINE %s: %s" % (error.line, error.message.encode("utf-8")))
            return False
        except:
            logging.debug('Something strange...')
            self.textEdit_XSD.setText('Something strange...')
            return False
        else:
            self.textEdit_XSD.setText("Success")
            return True

    # -----------------------------------------------------------------------------
    def on_quit(self, q):
        self.app.quit()

    # -----------------------------------------------------------------------------
    def start_gui(self):
        self.show()
        self.app.exec_()

# -----------------------------------------------------------------------------

class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        keywordFormat = QtGui.QTextCharFormat()
        keywordFormat.setForeground(QtCore.Qt.darkBlue)
        keywordFormat.setFontWeight(QtGui.QFont.Bold)

        keywordPatterns = ["\\bchar\\b", "\\bclass\\b", "\\bconst\\b",
                "\\bdouble\\b", "\\benum\\b", "\\bexplicit\\b", "\\bfriend\\b",
                "\\binline\\b", "\\bint\\b", "\\blong\\b", "\\bnamespace\\b",
                "\\boperator\\b", "\\bprivate\\b", "\\bprotected\\b",
                "\\bpublic\\b", "\\bshort\\b", "\\bsignals\\b", "\\bsigned\\b",
                "\\bslots\\b", "\\bstatic\\b", "\\bstruct\\b",
                "\\btemplate\\b", "\\btypedef\\b", "\\btypename\\b",
                "\\bunion\\b", "\\bunsigned\\b", "\\bvirtual\\b", "\\bvoid\\b",
                "\\bvolatile\\b"]

        self.highlightingRules = [(QtCore.QRegExp(pattern), keywordFormat)
                for pattern in keywordPatterns]

        classFormat = QtGui.QTextCharFormat()
        classFormat.setFontWeight(QtGui.QFont.Bold)
        classFormat.setForeground(QtCore.Qt.darkMagenta)
        self.highlightingRules.append((QtCore.QRegExp("\\bQ[A-Za-z]+\\b"),
                classFormat))

        singleLineCommentFormat = QtGui.QTextCharFormat()
        singleLineCommentFormat.setForeground(QtCore.Qt.red)
        self.highlightingRules.append((QtCore.QRegExp("//[^\n]*"),
                singleLineCommentFormat))

        self.multiLineCommentFormat = QtGui.QTextCharFormat()
        self.multiLineCommentFormat.setForeground(QtCore.Qt.red)

        quotationFormat = QtGui.QTextCharFormat()
        quotationFormat.setForeground(QtCore.Qt.darkGreen)
        self.highlightingRules.append((QtCore.QRegExp("\".*\""),
                quotationFormat))

        functionFormat = QtGui.QTextCharFormat()
        functionFormat.setFontItalic(True)
        functionFormat.setForeground(QtCore.Qt.blue)
        self.highlightingRules.append((QtCore.QRegExp("\\b[A-Za-z0-9_]+(?=\\()"),
                functionFormat))

        self.commentStartExpression = QtCore.QRegExp("/\\*")
        self.commentEndExpression = QtCore.QRegExp("\\*/")

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QtCore.QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.commentStartExpression.indexIn(text)

        while startIndex >= 0:
            endIndex = self.commentEndExpression.indexIn(text, startIndex)

            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + self.commentEndExpression.matchedLength()

            self.setFormat(startIndex, commentLength,
                    self.multiLineCommentFormat)
            startIndex = self.commentStartExpression.indexIn(text,
                    startIndex + commentLength);


def main():
    log_viewer_starter = LogViewer(sys.argv)

    log_viewer_starter.start_gui()


if __name__ == "__main__":
    main()
