#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk

# this reference may be necessary to help dynamically set the treeview store model
#http://stackoverflow.com/questions/6819271/change-gtkliststore-model-dynamically

class TreeViewColumnExample(object):

    # close the window and quit
    def delete_event(self, widget, event, data=None):
        
        # clean up
        gtk.main_quit()
        return False

    def __init__(self):
        
        # Create a new window and title it
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("CSV Paster")
                
        # create a liststore with string columns to use as the model
        self.liststore = gtk.ListStore(str,str) #gtk.ListStore(*[str]*len(data[0]))
        self.liststore.append(["Click me to paste in", "Or me!"])
        
        # create a CellRenderers to render the data
        self.cell = gtk.CellRendererText()

        # create the TreeView using liststore
        self.treeview = gtk.TreeView(self.liststore)
        col = gtk.TreeViewColumn("INIT")
        col.pack_start(self.cell, True)
        col.set_attributes(self.cell, text=0)
        col2 = gtk.TreeViewColumn("INIT2")
        col2.pack_start(self.cell, True)
        col2.set_attributes(self.cell, text=1)
        self.treeview.append_column(col)
        self.treeview.append_column(col2)
        
        # create the vbox to hold the treeview and other buttons
        self.vbox = gtk.VBox(homogeneous=False, spacing=4)
        self.vbox.pack_start(self.treeview)
        
        # add the main vbox to the window
        self.window.add(self.vbox)
        self.window.show_all()
        
        # connect signals
        self.window.connect("delete_event", self.delete_event)
        self.treeview.connect("button-press-event", self.treeview_click)
                
    def treeview_click(self, widget, event):
        
        # call the paste routine
        self.pasteIn() 
        
    def pasteIn(self):
        
        # use this for testing
        #data = [ ["1","2","3"], ["4","5","6","7"] ]
        
        # get the text from the clipboard, if it exists
        clipboard = gtk.clipboard_get()
        text = clipboard.wait_for_text()
        if text == None:
            return #...some warning
            
        # split it into rows, remove blank rows
        rows = text.split('\n')
        rows = [x for x in rows if x]
        
        # process the rows into individual csv lists, count the max # columns
        data_raw = []
        maxLen = 0
        for row in rows:
            vals = row.split(",")
            maxLen = max(len(vals), maxLen)
            data_raw.append(vals)   
            
        # pad each row to the maximum # columns
        data = []
        for row in data_raw:
            row2 = row+['']*(maxLen-len(row))
            data.append(row2)
       
        # create a new list store sized to this data
        self.liststore = gtk.ListStore(*[str]*len(data[0]))
        
        # reset the treeview to this liststore
        self.treeview.set_model(self.liststore)
        
        # remove all the columns from the treeview
        for col in self.treeview.get_columns():
            self.treeview.remove_column(col)
       
        # instantiate a stored columns array in case we need to access them after the fact
        self.columns = []
             
        # create columns for the table
        for i in range(len(data[0])):
            self.columns.append(gtk.TreeViewColumn(str(i+1)))
            self.treeview.append_column(self.columns[-1])
            self.columns[-1].pack_start(self.cell, True)
            self.columns[-1].set_attributes(self.cell, text=i)

        # now append the rows
        for datum in data:
            self.liststore.append(datum)
                      
        # Allow sorting on the column
        self.columns[0].set_sort_column_id(0)

def main():
    
    # run gtk to process messages
    gtk.main()

if __name__ == "__main__":
    
    # create the example window
    tvcexample = TreeViewColumnExample()
    
    # then run it
    main()