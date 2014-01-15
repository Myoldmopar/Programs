#!/usr/bin/python

# dependencies:
#python-gobject maybe?
#python-gobject-dev maybe?
#gobject-introspection maybe?
#python-git (0.1.6)
#canto?

import git
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
        if os.path.exists(self.homeDir + "/Documents/ToDoList/todo.mkd"):
            self.menu_todo_item.show()
        self.menu_todo_item.connect("activate", self.openToDoList)
        
        # Push/Pull ToDo list
        self.menu_pull_todo = Gtk.MenuItem("Pull ToDo List")
        self.menu.append(self.menu_pull_todo)
        if os.path.exists(self.homeDir + "/Documents/ToDoList/todo.mkd"):
            self.menu_pull_todo.show()
        self.menu_pull_todo.connect("activate", self.pullToDoList)
        self.menu_push_todo = Gtk.MenuItem("Push ToDo List")
        self.menu.append(self.menu_push_todo)
        if os.path.exists(self.homeDir + "/Documents/ToDoList/todo.mkd"):
            self.menu_push_todo.show()
        self.menu_push_todo.connect("activate", self.pushToDoList)
        
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
        
        self.menu_rsyncNRELhome_item = Gtk.MenuItem("Rsync NREL HOME to Server")
        self.menu.append(self.menu_rsyncNRELhome_item)
        self.menu_rsyncNRELhome_item.show()
        self.menu_rsyncNRELhome_item.connect("activate", self.rsyncNRELhome)
            
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
        if os.path.exists(self.homeDir + "/Documents/ToDoList/todo.mkd"):
            os.system("xdg-open " + self.homeDir + "/Documents/ToDoList/todo.mkd")
     
    def pushToDoList(self, widget):
        r = git.Repo('/home/elee/Documents/ToDoList')
        if r.is_dirty:
            g = git.Git('/home/elee/Documents/ToDoList')
            g.execute(['git','commit', '-a', '-m UpdatedToDoList'])
            g.execute(['git','push'])
            self.notif = Notify.Notification.new("To-do List Status", "Changes pushed...", "") 
        else:
            self.notif = Notify.Notification.new("To-do List Status", "No changes to push...", "") 
        self.notif.show()

    def pullToDoList(self, widget):
        g = git.Git('/home/elee/Documents/ToDoList')
        g.execute(['git', 'pull'])
        self.notif = Notify.Notification.new("To-do List Status", "Changes pulled...", "") 
        self.notif.show()
     
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
               
    def mountNREL(self, widget):
        os.system('MountNREL mount')
        
    def umountNREL(self, widget):
        os.system('MountNREL umount')
        
    def rsyncNRELhome(self, widget):
        os.system('gnome-terminal -e "rsync -rauW --progress NREL_ToSync/HOME NREL" --window-with-profile=HoldOpen')
            
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
