#!/usr/bin/python

# dependencies:
#python-gobject maybe?
#python-gobject-dev maybe?
#gobject-introspection maybe?
#canto?

import os
import sys
from gi.repository import Dbusmenu, Unity, GObject, Notify, Gtk, AppIndicator3 as appindicator
import webbrowser
from multiprocessing import Process

class my(object):
    
    def destroy(self, widget):
        exit()

    def __init__(self):
        
        # init some global "constants"
        self.appname = "indicator-my"
        self.homeDir = os.getenv('HOME')
                
        # init the notification system
        Notify.init(self.appname)
        self.notif = Notify.Notification.new("Starting MY Ubuntu!", "Habanada!", "") 
        self.notif.show()
        
        # set up the launcher
        self.launcher = Unity.LauncherEntry.get_for_desktop_id("my.desktop")
            
        # initi the gtk menu
        self.init_menu()
        
        # init the app-indicator ability
        self.ind = appindicator.Indicator.new(self.appname, "indicator-my", appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_title("indicator-my")
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_menu(self.menu)
        
        # update the indicator label with new data
        self.ind.set_icon_full(self.homeDir + "/Pictures/ubuntu.png", "my.desktop")

        # we'll also do some other Unity mods
        self.myChrome()
                
    def init_menu(self):
        
        # create a gtkMenu for the appindicator
        self.menu = Gtk.Menu()
                    
        # gmail item
        self.menu_gmail_item = Gtk.MenuItem("Open GMail")
        self.menu.append(self.menu_gmail_item)
        self.menu_gmail_item.show()
        self.menu_gmail_item.connect("activate", self.openGMail2)
    
        # ToDo list item
        self.menu_todo_item = Gtk.MenuItem("Open ToDo List")
        self.menu.append(self.menu_todo_item)
        if os.path.exists(self.homeDir + "/Documents/ToDoList/todo.todo"):
            self.menu_todo_item.show()
        self.menu_todo_item.connect("activate", self.openToDoList)
    
        # canto RSS reader item
        self.menu_rss_item = Gtk.MenuItem("Run Canto RSS Reader")
        self.menu.append(self.menu_rss_item)
        self.menu_rss_item.show()
        self.menu_rss_item.connect("activate", self.forkCanto)
    
        # separator for cleanliness
        self.menu_sep_item = Gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item)
        self.menu_sep_item.show()
    
        # mouse probing
        self.menu_mouseProbe_item = Gtk.MenuItem("Install Logitech Mouse Driver")
        self.menu.append(self.menu_mouseProbe_item)
        self.menu_mouseProbe_item.show()
        self.menu_mouseProbe_item.connect("activate", self.mouseProbe)
        
        # separator for cleanliness
        self.menu_sep_item2 = Gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item2)
        self.menu_sep_item2.show()
    
        # NREL Mount/Unmount
        self.menu_mountNREL_item = Gtk.MenuItem("Mount NREL Shares")
        self.menu.append(self.menu_mountNREL_item)
        self.menu_mountNREL_item.show()
        self.menu_mountNREL_item.connect("activate", self.mountNREL)
        
        self.menu_umountNREL_item = Gtk.MenuItem("Unmount NREL Shares")
        self.menu.append(self.menu_umountNREL_item)
        self.menu_umountNREL_item.show()
        self.menu_umountNREL_item.connect("activate", self.umountNREL)
            
        # separator for cleanliness
        self.menu_sep_item3 = Gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item3)
        self.menu_sep_item3.show()
                   
        # quit item
        self.menu_quit_item = Gtk.MenuItem("Quit")
        self.menu.append(self.menu_quit_item)
        self.menu_quit_item.show()
        self.menu_quit_item.connect("activate",self.destroy)
   
    def openToDoList(self, widget):
        if os.path.exists(self.homeDir + "/Documents/ToDoList/todo.todo"):
            os.system("xdg-open " + self.homeDir + "/Documents/ToDoList/todo.todo")
     
    def myChrome(self):
        self.chromeDesktop = Unity.LauncherEntry.get_for_desktop_id("google-chrome.desktop")
        self.chromeql = Dbusmenu.Menuitem.new()
        self.chromeitem0 = Dbusmenu.Menuitem.new()
        self.chromeitem0.property_set(Dbusmenu.MENUITEM_PROP_LABEL, "Open GMail")
        self.chromeitem0.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        self.chromeitem0.connect("item-activated", self.openGMail)
        self.chromeql.child_append(self.chromeitem0)
        self.chromeDesktop.set_property("quicklist", self.chromeql)        
            
    def openGMail(self, a, b):
        webbrowser.open("http://mail.google.com")

    def openGMail2(self, widget):
        webbrowser.open("http://mail.google.com")
    
    def forkCanto(self, widget):
        p = Process(target=self.runCanto)
        p.start()
    
    def runCanto(self):
        os.system('gnome-terminal -e "canto" --geometry=150x40')
            
    def mouseProbe(self, widget):
        os.system('reinstallLogitechMouseModule')
        
    def mountNREL(self, widget):
        os.system('MountNREL mount')
        
    def umountNREL(self, widget):
        os.system('MountNREL umount')
            
if __name__ == "__main__":     
    
    # check for another running instance   
    import fcntl
    lock_file = os.getenv('HOME') + '/.indicator-my.lock'
    fp = open(lock_file, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        # another instance is running
        exit()
    
    # it's ok, run!
    my()
    GObject.MainLoop().run()
