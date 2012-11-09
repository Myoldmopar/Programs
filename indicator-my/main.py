#!/usr/bin/python

# dependencies:
#python-gobject maybe?
#python-gobject-dev maybe?
#gobject-introspection maybe?

from gi.repository import Notify
import appindicator
import gtk
import time
import gobject
import os
import sys

class Weather(object):
    
    def destroy(self, widget):
        gtk.main_quit()

    def __init__(self):
        
        # init some global "constants"
        self.appname = "indicator-my"
        
        # init the notification system
        Notify.init(self.appname)
        
        # initi the gtk menu
        self.init_menu()
        
        # init the app-indicator ability
        self.ind = appindicator.Indicator(self.appname,"", appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_menu(self.menu)
        # update the indicator label with new data
        self.ind.set_label("MY")
        
    def init_menu(self):
        
        # create a gtkMenu for the appindicator
        self.menu = gtk.Menu()
                
        # suspend item - ensuring LID0 is DISABLED in /proc/acpi/wakeup
        self.menu_suspend_lid_item = gtk.MenuItem("Suspend - disable LID0")
        self.menu.append(self.menu_suspend_lid_item)
        self.menu_suspend_lid_item.show()
        self.menu_suspend_lid_item.connect("activate",self.suspendlid)

        # separator for cleanliness
        self.menu_sep_item = gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item)
        self.menu_sep_item.show()
               
        # quit item
        self.menu_quit_item = gtk.MenuItem("Quit")
        self.menu.append(self.menu_quit_item)
        self.menu_quit_item.show()
        self.menu_quit_item.connect("activate",self.destroy)
            
    def suspendlid(self, widget):
        os.system("gksudo /home/edwin/bin/suspendLID.sh")  
            
    def main(self):
        gtk.main()

if __name__ == "__main__":        
    Weather().main()
