#!/usr/bin/env python3
import sys
import os
from random import randint

from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox, QFileDialog, QTreeWidgetItem, QStyledItemDelegate, QFileDialog
)
from PyQt5.Qt import *
from PyQt5.QtCore import *

from PyQt5.uic import loadUi
from main_window_ui import Ui_MainWindow

from time import sleep
from pycore.core import fsutil

colors = [("Red",            "#FF0000"),
          ("Green",          "#00FF00"),
          ("Blue",           "#0000FF"),
          ("Black",          "#000000"),
          ("White",          "#FFFFFF"),
          ("Electric Green", "#41CD52"),
          ("Dark Blue",      "#222840"),
          ("Yellow",         "#F9E56d")]

modArchive = dict()

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
        self._fname = 'tmp.config.json'
        
    def run( self ):
        global modArchive

        modArchive = dict()
        
        for i, fname in enumerate( fsutil.yieldall( self._archivePath, '*' ) ):
            modArchive[ fname ] = dict()
            modArchive[ fname ][ 'linked' ] = False
            #self.progress.emit( i + 1 )
            
        self.finished.emit()


class ReadOnlyDelegate( QStyledItemDelegate ):
    def createEditor( self, parent, option, index ):
        return
    
class Window( QMainWindow, Ui_MainWindow ):
    def __init__( self, parent = None ):
        super().__init__(parent)
        self.setupUi(self)
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

    def reportProgress( self, n ):
        print( n )
        
    def connectSignalSlots(self ):
        self.actionNew.triggered.connect( self.new_config )
        self.actionLoad.triggered.connect( self.load )
        self.actionSave.triggered.connect( self.save )
        self.actionExit.triggered.connect( self.close )

    def initTable(self):
        self.readonly_delegate = ReadOnlyDelegate( self.tableWidget )
        
        self.tableWidget.setRowCount( len( colors ) )
        self.tableWidget.setColumnCount( len( colors[ 0 ] ) +1 )
        self.tableWidget.setHorizontalHeaderLabels( ["Name", "Hex Code", "Colors" ] )

        # Init data
        for i, (name, code ) in enumerate( colors ):
            item_name = QTableWidgetItem( name )
            #item_name.setFlags( item_name.flags() & ~Qt.ItemIsEnabled ) #Enable
            #item_name.setFlags( item_name.flags() & ~Qt.ItemIsEditable )

            
            
            item_code = QTableWidgetItem( code )
            item_color = QTableWidgetItem()
            item_color.setBackground( get_rgb_from_hex( code ) )
            item_color.setFlags( item_color.flags() | Qt.ItemIsUserCheckable )
            item_color.setCheckState( Qt.Unchecked )
            
            self.tableWidget.setItem( i, 0, item_name )
            self.tableWidget.setItem( i, 1, item_code )
            self.tableWidget.setItem( i, 2, item_color )
            

        self.tableWidget.setItemDelegateForColumn( 0, self.readonly_delegate )
        self.tableWidget.setItemDelegateForColumn( 1, self.readonly_delegate )


    def new_config( self ):
        global modArchive
        print( 'ModArchive = [{}]'.format( modArchive ) )
        self.archivePath = self.modArchivePathEdit.text()
        self.modPath     = self.modFolderPathEdit.text()

        if self.archivePath == '' or self.modPath == '':
            print( 'error' )
            # Add popup here

        # Create a placeholder file name
        self.config_file = 'tmp.config.json'
        self.create_worker( ConfigBuilder, archivePath = self.archivePath )       
        print( 'ModArchive = [{}]'.format( modArchive ) )
            
        
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
