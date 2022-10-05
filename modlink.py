#!/usr/bin/env python3
import sys
import os
import json
from random import randint

from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox, QFileDialog, QTreeWidgetItem, QStyledItemDelegate, QFileDialog
)
from PyQt5.Qt import *
from PyQt5.QtCore import *

from PyQt5.uic import loadUi
from main_window_ui import Ui_MainWindow
#from settings_window_ui import Ui_SettingsWindow
from settings_window_ui import Ui_SettingsDialog

from time import sleep
from pycore.core import fsutil

DEBUG = True
if DEBUG:
    def pyqt_set_trace():
        from PyQt5.QtCore import pyqtRemoveInputHook
        from pdb import set_trace
        pyqtRemoveInputHook()
        set_trace()

colors = [("Red",            "#FF0000"),
          ("Green",          "#00FF00"),
          ("Blue",           "#0000FF"),
          ("Black",          "#000000"),
          ("White",          "#FFFFFF"),
          ("Electric Green", "#41CD52"),
          ("Dark Blue",      "#222840"),
          ("Yellow",         "#F9E56d")]

modArchive = dict()

TMP_FILE='tmp.config.json'
DEFAULT_SETTINGS_DIR  = os.path.expanduser( '~/.modlink' )
DEFAULT_SETTINGS_FILE = 'settings.ini'
DEFAULT_SETTINGS_PATH = os.path.join( DEFAULT_SETTINGS_DIR, DEFAULT_SETTINGS_FILE )

default_paths = {
            "ModArchivePath": "/home/ryan/.modlink/archive",
            "ModInstallPath": "/home/ryan/.modlink/install",
            "TmpPath"       : "/home/ryan/.modlink/tmp"
    }

qsettings = QSettings( 'modlink', 'settings' )

def get_rgb_from_hex(code):
    code_hex = code.replace("#", "")
    rgb = tuple(int(code_hex[i:i+2], 16) for i in (0, 2, 4))
    return QColor.fromRgb(rgb[0], rgb[1], rgb[2])

class Worker( QObject ):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def run( self ):
        for i in range( 5 ):
            sleep( 1 )
            self.progress.emit( i + 1 )

        self.finished.emit()


class ConfigBuilder( Worker ):
    def __init__( self, archivePath ):
        super( ConfigBuilder, self ).__init__()
        self._archivePath = archivePath
        self._fname = TMP_FILE

    def run( self ):
        global modArchive

        modArchive = dict()

        for i, fname in enumerate( fsutil.yieldall( self._archivePath, '*' ) ):
            modArchive[ fname ] = dict()
            modArchive[ fname ][ 'linked' ] = False
            self.progress.emit( i + 1 )

        with open( self._fname, 'w' ) as f:
            json.dump( modArchive, f, indent = 4, sort_keys = False )
        self.finished.emit()


class ReadOnlyDelegate( QStyledItemDelegate ):
    def createEditor( self, parent, option, index ):
        return

class Window( QMainWindow, Ui_MainWindow ):
    def __init__( self, parent = None ):
        super().__init__(parent)
        self.setupUi(self)
        self.initConfig()
        self.initTable()
        self.connectSignalSlots()
        self.workers = []
        self.threads = dict()

    def create_worker( self, _class, *args, **kwargs ):

        thread = QThread()
        if thread not in self.threads.keys():
            self.threads[ thread ] = []

        worker = _class( *args, **kwargs )
        self.threads[ thread ].append( worker )

        worker.moveToThread( thread )
        thread.started.connect( worker.run )
        worker.finished.connect( thread.quit )
        worker.finished.connect( worker.deleteLater )
        thread.finished.connect( thread.deleteLater )
        worker.progress.connect( self.reportProgress )

        thread.start()
        return worker

    def reportProgress( self, n ):
        print( n )

    def connectSignalSlots(self ):
        #self.actionNew.triggered.connect( self.new_config )
        self.actionLoad.triggered.connect( self.load )
        self.actionSave.triggered.connect( self.save )
        self.actionExit.triggered.connect( self.close )
        self.actionPreferences.triggered.connect( self.preferences )


    def initConfig(self, path = None):
        global qsettings
        self.settings = qsettings
        for key, value in default_paths.items():
            setting = 'Paths/{}'.format( key )
            if not self.settings.contains( setting ):
                print( 'Initializing {}: {}'.format( setting, value ) )
                self.settings.setValue( setting, value )
            
        print( self.settings.fileName() )
        path = DEFAULT_SETTINGS_PATH


    def initTable(self):
        global modArchive
        print( 'init Table' )
        self.readonly_delegate = ReadOnlyDelegate( self.tableWidget )

        is_empty = len( modArchive ) == 0
        
        if is_empty and os.path.exists( TMP_FILE ):
            print( 'Reading previous temp file' )
            with open( TMP_FILE, 'r' ) as f:
                modArchive = json.load( f )

        if is_empty:
            return

        rows = len( modArchive )
        first_item = next( iter( modArchive ) )
        columns = len( modArchive[ first_item ] ) + 1

        self.tableWidget.setRowCount( rows )
        self.tableWidget.setColumnCount( columns + 1 )
        self.tableWidget.setHorizontalHeaderLabels( ["Path", "Linked", "Enabled" ] )

        # Init modArchive
        for i, (path, settings) in enumerate( modArchive.items() ):
        #for i, (name, code ) in enumerate( colors ):
            item_path = QTableWidgetItem( path )
            linked = settings[ 'linked' ]
            if linked:
                state = Qt.Checked
                link_str = 'True'
            else:
                state = Qt.Unchecked
                link_str = 'False'

            item_linked = QTableWidgetItem( link_str )
            item_enabled = QTableWidgetItem()
            item_enabled.setFlags( item_enabled.flags() | Qt.ItemIsUserCheckable )

            item_enabled.setCheckState( state )
            self.tableWidget.setItem( i, 0, item_path )
            self.tableWidget.setItem( i, 1, item_linked )
            self.tableWidget.setItem( i, 2, item_enabled )


        self.tableWidget.setItemDelegateForColumn( 0, self.readonly_delegate )
        self.tableWidget.setItemDelegateForColumn( 1, self.readonly_delegate )
        self.tableWidget.cellChanged.connect( self.onCellChanged )

    def onCellChanged( self, row, column ):
        print( row, column )
        item = self.tableWidget.item( row, column )
        print( item )
        lastState = item.data( Qt.UserRole )
        currentState = item.checkState()
        if lastState != currentState:
            print( 'changed' )

        path    = self.tableWidget.item( row, 0 )
        linked  = self.tableWidget.item( row, 1 )
        enabled = self.tableWidget.item( row, 2 )
        print( path.text(), linked.text(), enabled.checkState()==Qt.Checked )


#        
#    def new_config( self ):
#        global modArchive
#        print( 'ModArchive = [{}]'.format( modArchive ) )
#        self.archivePath = self.modArchivePathEdit.text()
#        self.modPath     = self.modFolderPathEdit.text()
#
#        if self.archivePath == '' or self.modPath == '':
#            print( 'error' )
#            # Add popup here
#
#        # Create a placeholder file name
#        self.config_file = 'tmp.config.json'
#        worker = self.create_worker( ConfigBuilder, archivePath = self.archivePath )
#        worker.finished.connect( self.initTable )
#        print( 'ModArchive = [{}]'.format( modArchive ) )


    def installMod( self ):
        pass

    def uninstallMod( self ):
        pass

    def load( self ):
        print( 'load' )
        path = QFileDialog.getOpenFileName( self, 'Mod Configuration File', '*.*' )[0]
        #self.create_worker()
        pass

    def save( self ):
        print( 'Save' )
        pass

    def createLinks(self):
        print( 'ModArchive = [{}]'.format( modArchive ) )
        pass

    def clearLinks(self):
        print( 'ModArchive = [{}]'.format( modArchive ) )
        pass

    def updateModFolder(self):
        print( 'updateModFolder' )
        path = QFileDialog.getExistingDirectory( self, 'Mod Folder', 'All Directories' )
        self.modFolderPathEdit.setText( path )
        #self.create_worker()
        pass

    def updateArchiveFolder(self):
        print( 'updateArchiveFolder' )
        path = QFileDialog.getExistingDirectory( self, 'Mod Folder', 'All Directories' )
        self.modArchivePathEdit.setText( path )
        #self.create_worker()
        pass

    def preferences( self ):
        print( 'Opening preferences' )
        dialog = SettingsDialog( self )
        result = dialog.exec()
        if result == QDialog.Accepted:
            print( 'Accepted!!!!!' )


class SettingsDialog( QDialog ):
    def __init__(self, parent = None ):
        super().__init__( parent )
        self.ui = Ui_SettingsDialog()
        self.ui.setupUi( self )

    def reject( self ):
        print( 'rejected' )
        super().reject()

    def accept( self ):
        print( 'accpeted' )
        self.save()
        super().accept()

    def load( self ):
        path = QFileDialog.getOpenFileName( self, 'Mod Configuration File', '*.*' )[0]
        pyqt_set_trace()
        self.ui.settingsFilePathLineEdit.setText( path )
        print( 'Load Settings' )

    def browseArchivePath( self ):
        path = QFileDialog.getExistingDirectory( self, 'Mod Folder', 'All Directories' )
        self.ui.modArchivePathLineEdit.setText( path )

    def browseInstallPath( self ):
        path = QFileDialog.getExistingDirectory( self, 'Mod Folder', 'All Directories' )
        self.ui.modInstallPathLineEdit.setText( path )

    def browseTmpPath( self ):
        path = QFileDialog.getExistingDirectory( self, 'Mod Folder', 'All Directories' )
        self.ui.tmpPathLineEdit.setText( path )

    def save_as( self ):
        print( 'Mod Archive path :{} '.format( self.ui.modArchivePathLineEdit.text() ) )
        print( 'Mod Install path :{} '.format( self.ui.modInstallPathLineEdit.text() ) )
        print( 'Tmp path :{} '.format( self.ui.tmpPathLineEdit.text() ) )
        print( 'save as ')

    def create_paths( self ):
        global qsettings
        pyqt_set_trace()
        keys = [ path for path in qsettings.allKeys() if 'Paths/' in path ]
        for key in keys:
            path = qsettings.value( key )
            path = os.path.expanduser( path )
            print( 'Attempting to create path: {}'.format( path ) )
            fsutil.mkdir_p( path )

    def save( self ):
        global qsettings
        qsettings.setValue( 'Paths/ModArchivePath', os.path.expanduser( self.ui.modArchivePathLineEdit.text() ) )
        qsettings.setValue( 'Paths/ModInstallPath', os.path.expanduser( self.ui.modInstallPathLineEdit.text() ) )
        qsettings.setValue( 'Paths/TmpPath',        os.path.expanduser( self.ui.tmpPathLineEdit.text() ) )
        self.create_paths()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
