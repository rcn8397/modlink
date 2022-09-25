#!/usr/bin/env python3
import sys
import os
from random import randint

from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox, QFileDialog, QTreeWidgetItem, QStyledItemDelegate
)
from PyQt5.Qt import *
from PyQt5.QtCore import *

from PyQt5.uic import loadUi
from main_window_ui import Ui_MainWindow

colors = [("Red",            "#FF0000"),
          ("Green",          "#00FF00"),
          ("Blue",           "#0000FF"),
          ("Black",          "#000000"),
          ("White",          "#FFFFFF"),
          ("Electric Green", "#41CD52"),
          ("Dark Blue",      "#222840"),
          ("Yellow",         "#F9E56d")]

def get_rgb_from_hex(code):
    code_hex = code.replace("#", "")
    rgb = tuple(int(code_hex[i:i+2], 16) for i in (0, 2, 4))
    return QColor.fromRgb(rgb[0], rgb[1], rgb[2])

class ReadOnlyDelegate( QStyledItemDelegate ):
    def createEditor( self, parent, option, index ):
        return
    
class Window( QMainWindow, Ui_MainWindow ):
    def __init__( self, parent = None ):
        super().__init__(parent)
        self.setupUi(self)
        self.initTable()
        self.connectSignalSlots()

        
    def connectSignalSlots(self ):
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


    def load( self ):
        print( 'load' )        
        pass

    def save( self ):
        print( 'Save' )
        pass
    
    def createLinks(self):
        pass

    def clearLinks(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
