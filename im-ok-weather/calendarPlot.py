#!/usr/bin/env python
#
# [SNIPPET_NAME: Calendar/Date picker]
# [SNIPPET_CATEGORIES: PyQt4]
# [SNIPPET_DESCRIPTION: A calendar/date picker example]
# [SNIPPET_AUTHOR: Darren Worrall <dw@darrenworrall.co.uk>]
# [SNIPPET_LICENSE: GPL]
# [SNIPPET_DOCS: http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qcalendarwidget.html]

# example calendar.py

import sys
from datetime import timedelta
from PyQt4 import QtGui, QtCore

class CalendarPlot(QtGui.QWidget):
    """
    A QCalendarWidget example
    """

    def __init__(self):
        # create GUI
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle('Calendar widget')
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
        
        # Create a label which we will use to show the date a week from now
        self.lbl = QtGui.QLabel()
        self.vbox.addWidget(self.lbl)
        
        # Connect the clicked signal to the centre handler
        self.connect(self.cal, QtCore.SIGNAL('selectionChanged()'), self.date_changed)

    def onOK(self):
        print "OK, OK!"
        self.result = 'OK'
        self.close()
        
    def onCancel(self):
        print "Cancelled, fine!"
        self.result = 'CANCEL'
        self.close()
        
    def date_changed(self):
        """
        Handler called when the date selection has changed
        """
        # Fetch the currently selected date, this is a QDate object
        date = self.cal.selectedDate()
        # This is a gives us the date contained in the QDate as a native
        # python date[time] object
        pydate = date.toPyDate()
        # Calculate the date a week from now
        sevendays = timedelta(days=7)
        aweeklater = pydate + sevendays
        # Show this date in our label
        self.lbl.setText('The date in a week will be: %s' % aweeklater)


# If the program is run directly or passed as an argument to the python
# interpreter then create a Calendar instance and show it


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    gui = CalendarPlot()
    gui.show()
    #connect(gui, QtCore.SIGNAL('close()'), onFormClosed)
    app.exec_()
    print 'result = %s' % gui.result
    
