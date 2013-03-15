#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk

class TreeViewColumnExample(object):

    def __init__(self):
        
        # Create a new window and title it and center it
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("My Delimiter Bin")
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_default_size(500,350)
        self.window.set_icon_from_file("./icon/icon.png")
        
        # create a liststore with string columns to use as the model
        self.liststore = gtk.ListStore(str,str) 
        self.liststore.append(["Ctrl-V for CSV Data", "Ctl-T for TSV data"])
        
        # create a CellRenderers to render the data
        self.cell = gtk.CellRendererText()
        self.cellLeader = gtk.CellRendererText()
        self.cellLeader.set_property('cell-background', 'gray')
        self.cellLeader.set_property('xalign', 0.5)

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
        
        # create a scrollable container for the treeview
        self.scrollTree = gtk.ScrolledWindow()
        self.scrollTree.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.scrollTree.add(self.treeview)
        
        # create the buttons
        self.btnPasteCSV = gtk.Button(label="Paste CSV")
        self.btnPasteTSV = gtk.Button(label="Paste TSV")
        self.btnPasteHeader = gtk.Button(label="CSV Header")
        self.btnOK = gtk.Button(label="OK, Done")
                
        # create the button hbox
        self.buttonBox = gtk.HBox(homogeneous=False, spacing=4)
        self.buttonBox.pack_start(self.btnPasteCSV)
        self.buttonBox.pack_start(self.btnPasteTSV)
        self.buttonBox.pack_start(self.btnPasteHeader)
        self.buttonBox.pack_start(self.btnOK)
                
        # create the vbox to hold the treeview and other buttons
        self.vbox = gtk.VBox(homogeneous=False, spacing=4)
        self.vbox.pack_start(self.scrollTree)
        self.vbox.pack_start(self.buttonBox, False)
        
        # add the main vbox to the window
        self.window.add(self.vbox)
        self.window.show_all()
        
        # connect signals
        self.btnPasteCSV.connect("clicked", self.btnPasteCSV_clicked)
        self.btnPasteTSV.connect("clicked", self.btnPasteTSV_clicked)
        self.btnPasteHeader.connect("clicked", self.btnPasteHeader_clicked)
        self.btnOK.connect("clicked", self.btnOK_clicked)
        self.window.connect("delete_event", gtk.main_quit)
        self.treeview.connect("key-press-event", self.treeview_key)
                              
        # now run
        gtk.main()
                              
    def btnPasteCSV_clicked(self, widget):
        self.pasteIn()
                
    def btnPasteTSV_clicked(self, widget):
        self.pasteIn("\t")
        
    def btnOK_clicked(self, widget):
        gtk.main_quit()
        return False
        
    def btnPasteHeader_clicked(self, widget):
        
        # create the file chooser dialog
        chooser = gtk.FileChooserDialog(title="Choose a CSV file", action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        chooser.set_select_multiple(False)
        chooser.set_default_response(gtk.RESPONSE_OK)
        filefilter = gtk.FileFilter()
        filefilter.add_pattern("*.csv")
        chooser.add_filter(filefilter)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            fileName = chooser.get_filename()
            f = open(fileName)
            line = f.readline().replace(",","\n")
            f.close()
            self.pasteIn(dataIn=line)
        chooser.destroy()
        
    def treeview_key(self, widget, event):
        if event.state == gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK:
            if event.keyval == 118:
                self.pasteIn()
            elif event.keyval == 116:
                self.pasteIn("\t")
        
    def pasteIn(self, delimiter=",", dataIn=None):
        
        # use this for testing
        #data = [ ["1","2","3"], ["4","5","6","7"] ]
        
        # get the text from the clipboard, if it exists
        if not dataIn:
            clipboard = gtk.clipboard_get()
            text = clipboard.wait_for_text()
            if text == None:
                return #...some warning
        else:
            text = dataIn
            
        # split it into rows, remove blank rows
        rows = text.split('\n')
        rows = [x for x in rows if x]
        
        # process the rows into individual csv lists, count the max # columns
        data_raw = []
        maxLen = 0
        for row in rows:
            vals = row.split(delimiter)
            maxLen = max(len(vals), maxLen)
            data_raw.append(vals)   
            
        # pad each row to the maximum # columns
        data = []
        for row in data_raw:
            row2 = row+['']*(maxLen-len(row))
            data.append(row2)
       
        # create a new list store sized to this data
        self.liststore = gtk.ListStore(*[str]*(maxLen+1))
        
        # reset the treeview to this liststore
        self.treeview.set_model(self.liststore)
        
        # remove all the columns from the treeview
        for col in self.treeview.get_columns():
            self.treeview.remove_column(col)
                    
        # add a row number column
        col = gtk.TreeViewColumn("Row")
        col.pack_start(self.cellLeader, True)
        col.set_attributes(self.cellLeader, text=0)
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(50)
        col.set_alignment(0.5)
        self.treeview.append_column(col)
        
        # create columns for the table
        count = 0
        for i in range(len(data[0])):
            count += 1
            col = gtk.TreeViewColumn(str(i+1))
            col.pack_start(self.cell, True)
            col.set_attributes(self.cell, text=i+1)
            col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            col.set_fixed_width(100)
            if count == 1:
                col.set_sort_column_id(1)
            self.treeview.append_column(col)
            
        # now append the rows
        rowNum = 0
        for datum in data:
            rowNum += 1
            self.liststore.append([rowNum] + datum)

if __name__ == "__main__":
    
    # create the example window
    tvcexample = TreeViewColumnExample()
 
