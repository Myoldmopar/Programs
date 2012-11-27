#!/usr/bin/python

from gi.repository import Unity, GObject, Dbusmenu, Notify, Gtk, AppIndicator3 as appindicator

class AppIndicator():
    
    def __init__(self):        
        # build the app indicator
        self.ind = appindicator.Indicator.new("example-simple-client", "", appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status (appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_attention_icon ("indicator-messages-new")
        self.ind.set_label("--TestApp--", "")        
        # create a menu
        self.menu = Gtk.Menu()
        self.build_menu(self.menu)
        self.ind.set_menu(self.menu)
    
    def menuitem_response(self, w, buf):
        # just print the string
        print "AppIndicator item handler: item=" + buf
        
    def done(self, w):    
        # exit the program
        print "Quitting!"
        exit()
        
    def build_menu(self, menu):
        # create item 1
        nm = "item 1"
        menu_item = Gtk.MenuItem(nm)
        self.menu.append(menu_item)
        menu_item.connect("activate", self.menuitem_response, "item 1")
        menu_item.show()
        # create item 2
        nm = "item 2"
        menu_item = Gtk.MenuItem(nm)
        self.menu.append(menu_item)
        menu_item.connect("activate", self.menuitem_response, "item 2")
        menu_item.show()  
        # a separator to make it look nice
        separator = Gtk.SeparatorMenuItem()
        self.menu.append(separator)
        separator.show()
        # and a quit item
        nm = "Quit"
        menu_item = Gtk.MenuItem(nm)
        self.menu.append(menu_item)
        menu_item.connect("activate", self.done)
        menu_item.show()
  
class Notification():
    
    def __init__(self):
        # init the notification library
        Notify.init("TestApp")  
        self.notif = Notify.Notification.new("Initial Notification", "This is the first notification", "") 
        self.notif.show()
        # then set up the timer to show another 5 seconds
        self.timer = GObject.timeout_add_seconds(5, self.showNextNotify)
       
    def showNextNotify(self):
        self.notif.update("Updated Notification", "This is an additional notification", "") 
        self.notif.show()
        return False # this should stop it, if we return True then it will tell it to keep showing
  
class UnityIntegration():
    
    def __init__(self):

        # Pretend to be an actual program for the sake of the example 
        self.launcher = Unity.LauncherEntry.get_for_desktop_id ("test.desktop")

        # Initially show a count of 0 on the icon
        self.launcher.set_property("count", 0)
        self.launcher.set_property("count_visible", True)

        # Set progress to 42% done 
        self.launcher.set_property("progress", 0.42)
        self.launcher.set_property("progress_visible", True)

        # We also want a quicklist 
        ql = Dbusmenu.Menuitem.new ()
        item1 = Dbusmenu.Menuitem.new ()
        item1.property_set (Dbusmenu.MENUITEM_PROP_LABEL, "Item 1")
        item1.property_set_bool (Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        item1.connect("item-activated", self.itemhandler)
        item2 = Dbusmenu.Menuitem.new ()
        item2.property_set (Dbusmenu.MENUITEM_PROP_LABEL, "Item 2")
        item2.property_set_bool (Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        item2.connect("item-activated", self.itemhandler)
        ql.child_append (item1)
        ql.child_append (item2)
        self.launcher.set_property("quicklist", ql)

        # init a counter
        self.counter = 0
        
        # start a loop to update the icon every 2 seconds
        GObject.timeout_add_seconds(2, self.update_launcher)

    def itemhandler(self, a, b):
        print "Dynamic quicklist handler: item=" + a.property_get(Dbusmenu.MENUITEM_PROP_LABEL)

    def update_launcher(self):
        
        # increment the counter, and update the count badge
        self.counter = self.counter + 1
        self.launcher.set_property("count", self.counter)
        
        # if we are on a multiple of 4 then update the icon's 'urgent' status
        if self.counter % 4 == 0:
            newStatus = not self.launcher.get_property("urgent")
            self.launcher.set_property("urgent", newStatus)
            
        # return True so that the loop will continue counting
        return True
  
if __name__ == "__main__":
  
    # set up each individual piece of the integration puzzle
    AppIndicator()
    Notification()
    UnityIntegration()
    
    # print for information
    print "Demonstrating Ubuntu Integration...press Ctrl-C to exit or use the indicator menu icon (top right)"
    
    # run the message loop! (pump/process messages)
    GObject.MainLoop().run()
