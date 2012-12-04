#!/usr/bin/python

# dependencies:
#python-gobject maybe?
#python-gobject-dev maybe?
#gobject-introspection maybe?

import os
import sys
from gi.repository import Dbusmenu, Unity, GObject, Notify, Gtk, AppIndicator3 as appindicator

class my(object):
    
    def destroy(self, widget):
        exit()

    def __init__(self):
        
        # init some global "constants"
        self.appname = "indicator-my"
        self.homeDir = os.getenv('HOME')
                
        # init the notification system
        Notify.init(self.appname)
        self.notif = Notify.Notification.new("Starting MY Ubuntu!", "This is gonna be great!", self.homeDir + "/bin/my.png") 
        self.notif.show()
        
        # set up the launcher
        self.launcher = Unity.LauncherEntry.get_for_desktop_id("my.desktop")
            
        # initi the gtk menu
        self.init_menu()
        
        # init quicklist
        self.init_quicklist()
        
        # init the app-indicator ability
        self.ind = appindicator.Indicator.new(self.appname,"", appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_menu(self.menu)
        
        # update the indicator label with new data
        self.ind.set_label("MY", "")
        
    def init_menu(self):
        
        # create a gtkMenu for the appindicator
        self.menu = Gtk.Menu()
                
        # suspend item - ensuring LID0 is DISABLED in /proc/acpi/wakeup
        self.menu_suspend_lid_item = Gtk.MenuItem("Suspend - disable LID0")
        self.menu.append(self.menu_suspend_lid_item)
        self.menu_suspend_lid_item.show()
        self.menu_suspend_lid_item.connect("activate", self.suspendlid)

        # timer item 
        self.menu_quick_timer_item = Gtk.MenuItem("Quick 15-min Timer")
        self.menu.append(self.menu_quick_timer_item)
        self.menu_quick_timer_item.show()
        self.menu_quick_timer_item.connect("activate", self.startTimer1)
    
        # ToDo list item
        self.menu_todo_item = Gtk.MenuItem("Open ToDo List")
        self.menu.append(self.menu_todo_item)
        if os.path.exists(self.homeDir + "/Documents/ToDoList/todo.todo"):
            self.menu_todo_item.show()
        self.menu_todo_item.connect("activate", self.openToDoList)
    
        # separator for cleanliness
        self.menu_sep_item = Gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item)
        self.menu_sep_item.show()
               
        # quit item
        self.menu_quit_item = Gtk.MenuItem("Quit")
        self.menu.append(self.menu_quit_item)
        self.menu_quit_item.show()
        self.menu_quit_item.connect("activate",self.destroy)
            
    def init_quicklist(self):
        self.ql = Dbusmenu.Menuitem.new()
        self.item0 = Dbusmenu.Menuitem.new()
        self.item0.property_set(Dbusmenu.MENUITEM_PROP_LABEL, "Turn on timer")
        self.item0.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        self.item0.connect("item-activated", self.startTimer2)
        self.ql.child_append(self.item0)
        self.item1 = Dbusmenu.Menuitem.new()
        self.item1.property_set(Dbusmenu.MENUITEM_PROP_LABEL, "Turn off timer")
        self.item1.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, False)
        self.item1.connect("item-activated", self.turnOffTimer)
        self.ql.child_append(self.item1)
        self.launcher.set_property("quicklist", self.ql)
            
    def suspendlid(self, widget):
        os.system("gksudo " + self.homeDir + "/bin/suspendLID.sh")  
    
    def startTimer(self):
        self.turnedOff = False
        self.counter = 15+1
        self.item0.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, False)
        self.item1.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        self.update_timer()
        GObject.timeout_add_seconds(60, self.update_timer)
        self.launcher.set_property("count_visible", True)
        
        #for quickitem in ql.get_children():
        #if quickitem.property_get('windowpath')==windowpath:
            #ql.child_delete(quickitem)
    
    def startTimer1(self, widget):
        self.startTimer()
    
    def startTimer2(self, a, b):
        self.startTimer()
        
    def update_timer(self):
        
        if self.turnedOff:
            return False
            
        # increment the counter, and update the count badge
        self.counter -= 1 
        self.launcher.set_property("count", self.counter)
        
        # if we are on a multiple of 4 then update the icon's 'urgent' status
        if self.counter <= 0:
            self.launcher.set_property("urgent", True)
            self.notif.update("Timer is done!", "Check the record!", "")
            self.notif.show()
            self.launcher.set_property("count_visible", False)
            ql = Dbusmenu.Menuitem.new()
            self.launcher.set_property("quicklist", ql)
            return False
        else:
            # return True so that the loop will continue counting
            return True
    
    def turnOffTimer(self, a, b):
        self.launcher.set_property("count_visible", False)
        self.item0.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        self.item1.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, False)
        self.turnedOff = True
    
    def openToDoList(self, widget):
        if os.path.exists(self.homeDir + "/Documents/ToDoList/todo.todo"):
            os.system("xdg-open " + self.homeDir + "/Documents/ToDoList/todo.todo")
            
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
