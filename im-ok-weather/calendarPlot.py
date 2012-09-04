
# imports
from PyQt4 import QtGui, QtCore

class CalendarPlot(QtGui.QWidget):

    def __init__(self):
        
        # create GUI
        QtGui.QMainWindow.__init__(self)
        
        # set the title
        self.setWindowTitle('Pick a day to plot the solar')
        
        # Set the window dimensions
        self.resize(300,175)
        
        # vertical layout for widgets
        self.vbox = QtGui.QVBoxLayout()
        self.setLayout(self.vbox)
        
        # Create a calendar widget and add it to our layout
        self.cal = QtGui.QCalendarWidget()
        self.vbox.addWidget(self.cal)

        # Create a space for two buttons: OK and cancel
        self.btnOK = QtGui.QPushButton("OK")
        self.connect(self.btnOK, QtCore.SIGNAL('clicked()'), self.onOK)
        self.btnCancel = QtGui.QPushButton('Cancel')
        self.connect(self.btnCancel, QtCore.SIGNAL('clicked()'), self.onCancel)
        self.btnBox = QtGui.QHBoxLayout()
        self.btnBox.addWidget(self.btnOK)
        self.btnBox.addWidget(self.btnCancel)
        self.vbox.addLayout(self.btnBox)
       
    def onOK(self):
        
        # leave a flag and close
        self.result = 'OK'
        self.close()
        
    def onCancel(self):
        
        # leave a flag and close
        self.result = 'CANCEL'
        self.close()
        
