#!/usr/bin/python

# dependencies:
#python-gobject maybe?
#python-gobject-dev maybe?
#gobject-introspection maybe?
#python-matplotlib (which depends on python and python-numpy)
#python-configobj (for config file)

from gi.repository import Notify
import re
import urllib
import appindicator
import gtk
from datetime import datetime
import time
import gobject
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from configobj import ConfigObj
import sys
import StringIO
import math

# a simple enum-only class
class StormTypes():
    NoStorms        = 0
    TornadoWarning  = 1
    sTornadoWarning = 'Tornado Warning'
    TornadoWatch    = 2
    sTornadoWatch   = 'Tornado Watch'
    TstormWarning   = 3
    sTstormWarning  = 'Severe Thunderstorm Warning'
    TstormWatch     = 4
    sTstormWatch    = 'Severe Thunderstorm Watch'

# solar position calculation class
class solarPosition(object):

    #' Reference:
    #'   McQuiston, F.C., J.D. Parker, J.D. Spitler.  2004.
    #'   Heating, Ventilating, and Air Conditioning Analysis and Design, Sixth Edition.
    #'   John Wiley and Sons, New York.
    
    def __init__(self, time, latitude, longitude, standardMeridian, DST_ON):
        
        # class constants
        self.degToRadians = 3.1415926535897931 / 180
        
        # set the time to use for all calculations
        self.thisTime = time
        
        # settings
        self.latitudeDeg = latitude #36.7 # degrees north
        self.longitudeDeg = longitude #97.2 # degrees west
        self.standardMeridianDeg = standardMeridian #90.0 # degrees west
        self.DST_ON = DST_ON
        
        # spew    
        self.output("Using date/time = %s" % self.thisTime)

        # conversions
        self.latitudeRad = self.latitudeDeg * self.degToRadians
        self.longitudeRad = self.longitudeDeg * self.degToRadians
        self.standardMeridianRad = self.standardMeridianDeg * self.degToRadians

        # daylight savings time adjustment
        if self.DST_ON == True:
            self.civilHour = self.thisTime.tm_hour - 1
        else:
            self.civilHour = self.thisTime.tm_hour
    
    def dayOfYear(self):
        dayOfYear = self.thisTime.tm_yday
        self.output("Day of year = %s" % dayOfYear)
        return dayOfYear

    def equationOfTime(self):
        radians = (self.dayOfYear() - 1.0) * (360.0/365.0) * self.degToRadians
        equationOfTimeMinutes = 229.2 * (0.000075 + 0.001868 * math.cos(radians) - 0.032077 * math.sin(radians) - 0.014615 * math.cos(2 * radians) - 0.04089 * math.sin(2 * radians))
        self.output("Equation of Time = %i minutes %i seconds" % (int(equationOfTimeMinutes), int((equationOfTimeMinutes-int(equationOfTimeMinutes))*60.0)))
        return equationOfTimeMinutes
        
    def declinationAngle(self):
        radians = (self.dayOfYear() - 1.0) * (360.0/365.0) * self.degToRadians
        decAngleDeg = 0.3963723 - 22.9132745 * math.cos(radians) + 4.0254304 * math.sin(radians) - 0.387205 * math.cos(2.0 * radians) + 0.05196728 * math.sin(2.0 * radians) - 0.1545267 * math.cos(3.0 * radians) + 0.08479777 * math.sin(3.0 * radians)
        decAngleRad = decAngleDeg * self.degToRadians
        self.output("Declination angle = %s degrees (%s radians)" % (decAngleDeg, decAngleRad))
        return [decAngleDeg, decAngleRad]

    def localCivilTime(self):
        localCivilTimeHours = self.civilHour + self.thisTime.tm_min/60.0 + self.thisTime.tm_sec/3600.0
        self.output("Local civil time = %s hours" % localCivilTimeHours)
        return localCivilTimeHours
        
    def localSolarTime(self):
        localSolarTimeHours = self.localCivilTime() - (self.longitudeDeg-self.standardMeridianDeg)*(4.0/60.0) + self.equationOfTime()/60.0
        self.output("Local solar time = %s hours" % localSolarTimeHours)
        return localSolarTimeHours
        
    def hourAngle(self):
        localSolarTimeHours = self.localSolarTime()
        hourAngleDeg = 15.0 * (localSolarTimeHours - 12)
        hourAngleRad = hourAngleDeg * self.degToRadians
        self.output("Hour angle = %s degrees (%s radians)" % (hourAngleDeg, hourAngleRad))
        return [hourAngleDeg, hourAngleRad]
        
    def altitudeAngle(self):
        altitudeAngleRadians = math.asin( math.cos(self.latitudeRad) * math.cos(self.declinationAngle()[1]) * math.cos(self.hourAngle()[1]) + math.sin(self.latitudeRad) * math.sin(self.declinationAngle()[1]) )
        altitudeAngleDegrees = altitudeAngleRadians / self.degToRadians
        self.output("Altitude angle = %s degrees (%s radians)" % (altitudeAngleDegrees, altitudeAngleRadians))
        return altitudeAngleDegrees
       
    def output(self, string):
        print string

# simple settings popup dialog
class settingsWindow(gtk.Window):
    
    def __init__(self, locations, initIndex, prevFreq):
        gtk.Window.__init__(self) 
        
        # initialization
        self.set_title("Update Settings")
        self.set_border_width(10)
        self.set_modal(True)
        meso_site_store = gtk.ListStore(str, str)
        for loc in locations:
            meso_site_store.append([loc[0], loc[1]]) 
        
        # site selection
        lblSite = gtk.Label()
        lblSite.set_label("Choose a Mesonet Site:")
        meso_site_combo = gtk.ComboBox(model=meso_site_store)
        meso_site_combo.connect("changed", self.on_name_combo_changed)
        meso_site_combo.set_active(initIndex)
        cell = gtk.CellRendererText()
        meso_site_combo.pack_start(cell, True)
        meso_site_combo.add_attribute(cell, "text", 1)
        hbox_site = gtk.HBox(spacing=6)
        hbox_site.pack_start(lblSite)
        hbox_site.pack_start(meso_site_combo)
        
        # update frequency
        lblFreq = gtk.Label()
        lblFreq.set_label("Select Update Frequency [ms] (5 minutes = 300,000):")
        self.freqEntry = gtk.Entry()
        self.freqEntry.set_text(str(prevFreq))
        self.freqEntry.connect("changed", self.onEntryChanged)
        hbox_freq = gtk.HBox(spacing=6)
        hbox_freq.pack_start(lblFreq)
        hbox_freq.pack_start(self.freqEntry)
        
        # form buttons
        self.btnOK = gtk.Button(stock = gtk.STOCK_OK)
        self.btnOK.connect("clicked", self.onOK)
        btnCancel = gtk.Button(stock = gtk.STOCK_CANCEL)
        btnCancel.connect("clicked", self.onCancel)
        hbox_btns = gtk.HBox(spacing=6)
        hbox_btns.pack_start(self.btnOK)
        hbox_btns.pack_start(btnCancel)
                
        # vbox to hold everything
        vbox = gtk.VBox(spacing=6)       
        vbox.pack_start(hbox_site, False, False, 0)
        vbox.pack_start(hbox_freq, False, False, 0)
        vbox.pack_start(hbox_btns, False, False, 0) 
        self.add(vbox)
        
        # initialize a flag for parent
        self.applyChanges = False

    def on_name_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            self.ID = model[tree_iter][0]
            #print "Selected: ID=%s" % (self.ID)
        else:
            #print "Entered: %s" % entry.get_text()
            entry = combo.get_child()
      
    def onEntryChanged(self, entry):
        s = self.freqEntry.get_text()
        try:
            i = int(s)
            self.btnOK.set_label("OK")
            self.btnOK.set_sensitive(True)
        except:
            self.btnOK.set_label("Invalid Update Frequency")
            self.btnOK.set_sensitive(False)
            return
                    
    def onOK(self, widget):
        self.applyChanges = True
        self.hide()
        
    def onCancel(self, widget):
        self.applyChanges = False
        self.hide()

# the full weather program class
class Weather(object):
    
    def destroy(self, widget):
        gtk.main_quit()

    def __init__(self):
        
        # ---------------------- BEGIN ORDER-INDEPENDENT INITIALIZATION ----------------------- #
        # init some global "constants"
        self.appname = "im-ok-weather"
        self.unknown = "??"
        self.url = "http://www.mesonet.org/data/public/mesonet/current/current.csv.txt"
        self.degree_symbol = unichr(176)
        self.config_file_path = os.getenv("HOME") + "/.config/" + self.appname
        self.stdmeridian = 90
        self.storms = StormTypes()
        self.fillLocations()
        
        # init other global variables
        self.plotX = []
        self.plotY = []
        
        # init the notification system
        Notify.init(self.appname)
        self.notification = Notify.Notification.new('', '', '') 
        
        # init the gtk menu -- need to wait until we have 
        self.init_menu()
        
        # init the app-indicator ability
        self.ind = appindicator.Indicator("im-ok-weather","", appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_menu(self.menu)
        # ----------------------- END ORDER-INDEPENDENT INITIALIZATION ------------------------ #
        
        # ----------------------- BEGIN ORDER-DEPENDENT INITIALIZATION ------------------------ #
        # setup some default configurable parameters (may be overridden by contents of config file)
        self.update_interval_ms = 300000 # 3e5 ms = 300 seconds = 5 minutes = mesonet update frequency
        self.mesonet_location_tag = 'STIL'
                
        # override default configuration with saved data
        self.read_config_file()                
        
        # Update location-based info based on either default or overridden mesonet tag
        self.updateLocation(self.mesonet_location_tag)
                                    
        # do a refresh once initially
        self.do_a_refresh()
        # ------------------------ END ORDER-DEPENDENT INITIALIZATION ------------------------- #
                        
        # then set up the timer
        self.timer = gobject.timeout_add(self.update_interval_ms, self.do_a_refresh)
        
    def fillLocations(self):
        self.locations = []
        self.locations.append(["ADAX", "Ada", 34.8, 96.67])
        self.locations.append(["ALTU", "Altus", 34.59, 99.34])
        self.locations.append(["ARNE", "Arnett", 36.07, 99.9])
        self.locations.append(["BEAV", "Beaver", 36.8, -100.53])
        self.locations.append(["BESS", "Bessie", 35.4, 99.06])
        self.locations.append(["BIXB", "Bixby", 35.96, 95.87])
        self.locations.append(["BLAC", "Blackwell", 36.75, 97.25])
        self.locations.append(["BOIS", "Boise City", 36.69, -102.5])
        self.locations.append(["BOWL", "Bowlegs", 35.17, 96.63])
        self.locations.append(["BREC", "Breckinridge", 36.41, 97.69])
        self.locations.append(["BRIS", "Bristow", 35.78, 96.35])
        self.locations.append(["BUFF", "Buffalo", 36.83, 99.64])
        self.locations.append(["BURB", "Burbank", 36.63, 96.81])
        self.locations.append(["BURN", "Burneyville", 33.89, 97.27])
        self.locations.append(["BUTL", "Butler", 35.59, 99.27])
        self.locations.append(["BYAR", "Byars", 34.85, 97])
        self.locations.append(["CAMA", "Camargo", 36.03, 99.35])
        self.locations.append(["CENT", "Centrahoma", 34.61, 96.33])
        self.locations.append(["CHAN", "Chandler", 35.65, 96.8])
        self.locations.append(["CHER", "Cherokee", 36.75, 98.36])
        self.locations.append(["CHEY", "Cheyenne", 35.55, 99.73])
        self.locations.append(["CHIC", "Chickasha", 35.03, 97.91])
        self.locations.append(["CLAY", "Clayton", 34.66, 95.33])
        self.locations.append(["CLOU", "Cloudy", 34.22, 95.25])
        self.locations.append(["COOK", "Cookson", 35.68, 94.85])
        self.locations.append(["COPA", "Copan", 36.91, 95.89])
        self.locations.append(["DURA", "Durant", 33.92, 96.32])
        self.locations.append(["ELRE", "El Reno", 35.55, 98.04])
        self.locations.append(["ERIC", "Erick", 35.2, 99.8])
        self.locations.append(["EUFA", "Eufaula", 35.3, 95.66])
        self.locations.append(["FAIR", "Fairview", 36.26, 98.5])
        self.locations.append(["FORA", "Foraker", 36.84, 96.43])
        self.locations.append(["FREE", "Freedom", 36.73, 99.14])
        self.locations.append(["FTCB", "Fort Cobb", 35.15, 98.47])
        self.locations.append(["GOOD", "Goodwell", 36.6, -101.6])
        self.locations.append(["GUTH", "Guthrie", 35.85, 97.48])
        self.locations.append(["HASK", "Haskell", 35.75, 95.64])
        self.locations.append(["HINT", "Hinton", 35.48, 98.48])
        self.locations.append(["HOBA", "Hobart", 34.99, 99.05])
        self.locations.append(["HOLL", "Hollis", 34.69, 99.83])
        self.locations.append(["HOOK", "Hooker", 36.86, -101.23])
        self.locations.append(["HUGO", "Hugo", 34.03, 95.54])
        self.locations.append(["IDAB", "Idabel", 33.83, 94.88])
        self.locations.append(["JAYX", "Jay", 36.48, 94.78])
        self.locations.append(["KENT", "Kenton", 36.83, -102.88])
        self.locations.append(["KETC", "Ketchum Ranch", 34.53, 97.76])
        self.locations.append(["LAHO", "Lahoma", 36.38, 98.11])
        self.locations.append(["LANE", "Lane", 34.31, 96])
        self.locations.append(["MADI", "Madill", 34.04, 96.94])
        self.locations.append(["MANG", "Mangum", 34.84, 99.42])
        self.locations.append(["MARE", "Marena", 36.06, 97.21])
        self.locations.append(["MAYR", "May Ranch", 36.99, 99.01])
        self.locations.append(["MCAL", "McAlester", 34.88, 95.78])
        self.locations.append(["MEDF", "Medford", 36.79, 97.75])
        self.locations.append(["MEDI", "Medicine Park", 34.73, 98.57])
        self.locations.append(["MIAM", "Miami", 36.89, 94.84])
        self.locations.append(["MINC", "Minco", 35.27, 97.96])
        self.locations.append(["MTHE", "Mt Herman", 34.31, 94.82])
        self.locations.append(["NEWK", "Newkirk", 36.9, 96.91])
        self.locations.append(["NOWA", "Nowata", 36.74, 95.61])
        self.locations.append(["OILT", "Oilton", 36.03, 96.5])
        self.locations.append(["OKEM", "Okemah", 35.43, 96.26])
        self.locations.append(["OKMU", "Okmulgee", 35.58, 95.91])
        self.locations.append(["PAUL", "Pauls Valley", 34.72, 97.23])
        self.locations.append(["PAWN", "Pawnee", 36.36, 96.77])
        self.locations.append(["PERK", "Perkins", 36, 97.05])
        self.locations.append(["PRYO", "Pryor", 36.37, 95.27])
        self.locations.append(["PUTN", "Putnam", 35.9, 98.96])
        self.locations.append(["REDR", "Red Rock", 36.36, 97.15])
        self.locations.append(["RETR", "Retrop", 35.12, 99.36])
        self.locations.append(["RING", "Ringling", 34.19, 97.59])
        self.locations.append(["SALL", "Sallisaw", 35.44, 94.8])
        self.locations.append(["SEIL", "Seiling", 36.19, 99.04])
        self.locations.append(["SHAW", "Shawnee", 35.36, 96.95])
        self.locations.append(["SKIA", "Skiatook", 36.42, 96.04])
        self.locations.append(["SLAP", "Slapout", 36.6, -100.26])
        self.locations.append(["SPEN", "Spencer", 35.54, 97.34])
        self.locations.append(["STIG", "Stigler", 35.27, 95.18])
        self.locations.append(["STIL", "Stillwater", 36.12, 97.1])
        self.locations.append(["STUA", "Stuart", 34.88, 96.07])
        self.locations.append(["SULP", "Sulphur", 34.57, 96.95])
        self.locations.append(["TAHL", "Tahlequah", 35.97, 94.99])
        self.locations.append(["TALI", "Talihina", 34.71, 95.01])
        self.locations.append(["TIPT", "Tipton", 34.44, 99.14])
        self.locations.append(["TISH", "Tishomingo", 34.33, 96.68])
        self.locations.append(["VINI", "Vinita", 36.78, 95.22])
        self.locations.append(["WASH", "Washington", 34.98, 97.52])
        self.locations.append(["WATO", "Watonga", 35.84, 98.53])
        self.locations.append(["WAUR", "Waurika", 34.17, 97.99])
        self.locations.append(["WEAT", "Weatherford", 35.51, 98.78])
        self.locations.append(["WEST", "Westville", 36.01, 94.64])
        self.locations.append(["WILB", "Wilburton", 34.9, 95.35])
        self.locations.append(["WIST", "Wister", 34.98, 94.69])
        self.locations.append(["WOOD", "Woodward", 36.42, 99.42])
        self.locations.append(["WYNO", "Wynona", 36.52, 96.34])
        self.locations.append(["NINN", "Ninnekah", 34.97, 97.95])
        self.locations.append(["ACME", "Acme", 34.81, 98.02])
        self.locations.append(["APAC", "Apache", 34.91, 98.29])
        self.locations.append(["HECT", "Hectorville", 35.84, 96])
        self.locations.append(["ALV2", "Alva", 36.71, 98.71])
        self.locations.append(["GRA2", "Grandfield", 34.24, 98.74])
        self.locations.append(["PORT", "Porter", 35.83, 95.56])
        self.locations.append(["INOL", "Inola", 36.14, 95.45])
        self.locations.append(["NRMN", "Norman", 35.24, 97.46])
        self.locations.append(["CLRM", "Claremore", 36.32, 95.65])
        self.locations.append(["NEWP", "Newport", 34.23, 97.2])
        self.locations.append(["BROK", "Broken Bow", 34.04, 94.62])
        self.locations.append(["MRSH", "Marshall", 36.12, 97.61])
        self.locations.append(["ARD2", "Ardmore", 34.19, 97.09])
        self.locations.append(["FITT", "Fittstown", 34.55, 96.72])
        self.locations.append(["OKCN", "Oklahoma City North", 35.56, 97.51])
        self.locations.append(["OKCW", "Oklahoma City West", 35.47, 97.58])
        self.locations.append(["OKCE", "Oklahoma City East", 35.47, 97.46])
        self.locations.append(["CARL", "Lake Carl Blackwell", 36.15, 97.29])
        self.locations.append(["WEBR", "Webbers Falls", 35.49, 95.12])
        self.locations.append(["KIN2", "Kingfisher", 35.85, 97.95])
        self.locations.append(["HOLD", "Holdenville", 35.07, 96.36])
        self.locations.append(["ANT2", "Antlers", 34.25, 95.67])
        self.locations.append(["WAL2", "Walters", 34.4, 98.35])

    def read_config_file(self):
        if not os.path.exists(self.config_file_path):
            return          
        config = ConfigObj(self.config_file_path)
        self.update_interval_ms = int(config['update_interval_ms'])
        self.mesonet_location_tag = config['mesonet_location_tag']
        
    def write_config_file(self):
        config = ConfigObj(self.config_file_path)
        config['update_interval_ms'] = self.update_interval_ms
        config['mesonet_location_tag'] = self.mesonet_location_tag
        config.write()
        
    def init_menu(self):
        
        # create a gtkMenu for the appindicator
        self.menu = gtk.Menu()
                
        # force a refresh item
        self.menu_force_item = gtk.MenuItem("Refresh now")
        self.menu.append(self.menu_force_item)
        self.menu_force_item.show()
        self.menu_force_item.connect("activate", self.do_a_refresh)

        # plot history
        self.menu_plot_item = gtk.MenuItem("Plot history")
        self.menu.append(self.menu_plot_item)
        self.menu_plot_item.show()
        self.menu_plot_item.connect("activate", self.plot)

        # plot solar profile for today
        self.menu_solar_today_item = gtk.MenuItem("Plot today's solar")
        self.menu.append(self.menu_solar_today_item)
        self.menu_solar_today_item.show()
        self.menu_solar_today_item.connect("activate", self.plotSolarToday)

        # separator for cleanliness
        self.menu_sep_item = gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item)
        self.menu_sep_item.show()
        
        # current location item
        self.menu_cur_item = gtk.MenuItem("Current location keyword: %s" % "Initializing...")
        self.menu.append(self.menu_cur_item)
        self.menu_cur_item.show()
        
        # current location name
        self.menu_cur_item_name = gtk.MenuItem("Current location name: %s" % "Initializing...")
        self.menu.append(self.menu_cur_item_name)
        self.menu_cur_item_name.show()
        
        # current location location
        self.menu_cur_item_loc = gtk.MenuItem("Current location (lat,long): (%s, %s)" % ("...", "..."))
        self.menu.append(self.menu_cur_item_loc)
        self.menu_cur_item_loc.show()
                
        # current interval item
        self.menu_curtime_item = gtk.MenuItem("Current update interval: %sms" % "Initializing...")
        self.menu.append(self.menu_curtime_item)
        self.menu_curtime_item.show()
        
        # separator for cleanliness
        self.menu_sep_item2 = gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item2)
        self.menu_sep_item2.show()
        
        # updated time item
        self.menu_update_item = gtk.MenuItem("Initializing...")
        self.menu.append(self.menu_update_item)
        self.menu_update_item.show()
                
        # item to update settings
        self.menu_settings_item = gtk.MenuItem("Update settings...")
        self.menu.append(self.menu_settings_item)
        self.menu_settings_item.show()
        self.menu_settings_item.connect("activate", self.update_settings)
        
        # separator for cleanliness
        self.menu_sep_item3 = gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item3)
        self.menu_sep_item3.show()        
        
        # quit item
        self.menu_quit_item = gtk.MenuItem("Quit")
        self.menu.append(self.menu_quit_item)
        self.menu_quit_item.show()
        self.menu_quit_item.connect("activate", self.destroy)

    def init_dynamicSettings_menu(self):
        
        # current location item
        self.menu_cur_item.set_label("Current location keyword: %s" % self.mesonet_location_tag)
        self.menu_cur_item_name.set_label("Current location name: %s" % self.locale_name)
        self.menu_cur_item_loc.set_label("Current location (latitude, long): (%s, %s)" % (self.latitude, self.longitude))
        
        # current interval item
        self.menu_curtime_item.set_label("Current update interval: %sms" % self.update_interval_ms)

    def update_settings(self, widget):
        self.settings = settingsWindow(self.locations, self.mesonet_location_tag_index, self.update_interval_ms)
        self.settings.show_all()
        self.settings.connect("hide", self.handleClose)
        
    def handleClose(self, widget):
        if not self.settings.applyChanges:
            return
        self.updateLocation(self.settings.ID)
        
    def updateLocation(self, key):
        i = -1
        for loc in self.locations:
            i += 1
            if loc[0] == key:
                self.mesonet_location_tag = loc[0]
                self.mesonet_location_tag_index = i
                self.locale_name = loc[1]
                self.latitude = loc[2]
                self.longitude = loc[3]
                self.init_dynamicSettings_menu()
                self.county = self.getCounty()
                self.do_a_refresh()
                self.write_config_file()
                return
        # shouldn't get here
        print "Uh, oh! Bad key passed to updateLocation"
                
    def do_a_refresh(self, widget=None):
                
        try:        
            
            # open the site, and read the results into a variable
            f = urllib.urlopen(self.url)
            result = f.read()
            
            # split the result into a list, one item per line of the original data
            listA = result.split('\n')
            
            # parse out Stillwater's data
            expr = re.compile('^'+self.mesonet_location_tag)
            data = filter(expr.search,listA)
            tokens = [x.strip() for x in data[0].split(',')]
            
            # check if there is even an entry for this locale
            if tokens[1].strip() == '':
                self.ind.set_label(" No Data for: " + self.mesonet_location_tag)
                return
            
            # get this valid location name
            self.locale_name = tokens[1]
            
            # check each token, assign the unknown status if it is missing
            # dry bulb temperature
            if tokens[10].strip() == '':
                temp = self.unknown
            else:
                temp = int(tokens[10])
                
            # wind speed
            if tokens[16].strip() == '':
                windspeed = self.unknown
            else:
                windspeed = int(tokens[16])
                
            # wind direction
            if tokens[15].strip() == '':
                winddir = self.unknown
                arrow = ""
            else:
                winddir = str(tokens[15])
                # get a nice looking unicode arrow character based on wind direction
                arrow = self.get_arrow(winddir)
        
        except:
            
            temp = self.unknown
            windspeed = self.unknown
            winddir = self.unknown
            arrow = ""
            
        # create an update string
        sIndicator = " %s%sF  %s%s " % (str(temp), self.degree_symbol, str(windspeed), arrow)
        
        # this will be used a few times here
        thistime = datetime.now()
                
        # update the menu item to say we have updated
        self.menu_update_item.set_label(thistime.strftime("Updated at: %Y-%b-%d %H:%M:%S"))
        
        # check for severe weather
        theseWarnings = [] #self.getWatchWarnings()
                 
        # update the indicator label with new data
        self.ind.set_label(sIndicator)
        
        # send a notification message
        sNotify = "Temperature:\t%s\nWind Speed:\t%s\nWind Direction:\t%s" % (str(temp), str(windspeed), winddir)
        #print theseWarnings
        if not theseWarnings:
            self.notification.update(self.locale_name + " Weather Updated", sNotify, '') 
            self.notification.show()
        elif self.storms.TornadoWarning in theseWarnings:
            self.notification.update(self.locale_name + " Weather Updated", "TORNADO WARNING!", '') 
            self.notification.show()
        elif self.storms.TornadoWatch in theseWarnings:
            self.notification.update(self.locale_name + " Weather Updated", "Tornado Watch!", '') 
            self.notification.show()
        elif self.storms.TstormWarning in theseWarnings:
            self.notification.update(self.locale_name + " Weather Updated", "Severe Thunderstorm Warning!", '') 
            self.notification.show()
        elif self.storms.TstormWatch in theseWarnings:
            self.notification.update(self.locale_name + " Weather Updated", "Severe Thunderstorm Watch", '') 
            self.notification.show()
                
        # store the current time and temperature for plotting
        thistime_num = matplotlib.dates.date2num(thistime)
        self.plotX.append(thistime_num)
        self.plotY.append(temp)
                
        # callback return value, so that gobject knows it can continue cycling
        return True

    def get_arrow(self, dir):
        if dir == "N":
            arrow = u"\u2193" # downwards pointing arrow
        elif dir == "E":
            arrow = u"\u2190" # leftwards pointing arrow
        elif dir == "S":
            arrow = u"\u2191" # upwards pointing arrow
        elif dir == "W":
            arrow = u"\u2192" # rightwards pointing arrow
        elif dir in ["NE","NNE","ENE"]:
            arrow = u"\u2199" # southwest pointing arrow
        elif dir in ["NW", "WNW", "NNW"]:
            arrow = u"\u2198" # southeast pointing arrow
        elif dir in ["SE", "SSE", "ESE"]:
            arrow = u"\u2196" # northwest pointing arrow
        elif dir in ["SW", "SSW", "WSW"]:
            arrow = u"\u2197" # northeast pointing arrow
        else:
            print " Oops...bad wind direction passed to self.get_arrow(), dir = " + dir
        return arrow

    def plot(self, widget):
        plt.xlabel('Date/Time')
        plt.ylabel('Temperature [%sF]' % self.degree_symbol)
        plt.title('Recorded temperature history')
        plt.grid(True)
        plt.plot_date(self.plotX, self.plotY, fmt='bo', tz=None, xdate=True)
        plt.show()

    def getDST(self, year, month, date):
        retVal = False
        if year == 2012:
            if month == 3 and date >= 11:
                retVal = True
            elif month > 3 and month < 11:
                retVal = True
            elif month == 11 and date < 4:
                retVal = True
        else:
            print "DST not yet implemented for years other than 2012...fix me!...defaulting to not DST"
        return retVal

    def plotSolarToday(self, widget):
    
        # get the current day
        rightNow = time.localtime()
        # note that the fourth item below is actually an escaped percent sign!
        rightNowString = "%s-%s-%s %%s:00:00" % (rightNow.tm_year, rightNow.tm_mon, rightNow.tm_mday)
        DST = self.getDST(rightNow.tm_year, rightNow.tm_mon, rightNow.tm_mday)
        self.plotSolar(rightNowString, 'today', DST)
        
    def plotSolar(self, singleDayString, plotDateString, DSTFlag):
        
        #singleDayString should be of the form "YEAR-MONTH-DATE %s:00:00" so that the %s can be swept over 24 hours in a loop
        #plotDateString is just a label for the top of the plot
        
        # calculate the altitude angle for each hour (could do each half hour or whatever)
        altitudes = []
        for hour in range(0,24):
            #print hour
            thisTime = time.strptime(singleDayString % str(hour), "%Y-%m-%d %H:%M:%S")   
            solar = solarPosition(thisTime, self.latitude, self.longitude, self.stdmeridian, DSTFlag)
            beta = solar.altitudeAngle()
            altitudes.append(beta)
        #print altitudes

        # plot it!
        plt.xticks(np.arange(0,24,1))
        plt.xlabel('Hour of day')
        plt.ylabel('Solar Altitude Angle [%s]' % self.degree_symbol)
        plt.title('Solar Profile for %s' % plotDateString)
        plt.grid(True)
        plt.plot(altitudes)

        # add the current date-time / altitude, just for info
        rightNow = time.localtime()
        rightNowString = "%s-%s-%s %s:%s:00" % (rightNow.tm_year, rightNow.tm_mon, rightNow.tm_mday, rightNow.tm_hour, rightNow.tm_min)
        rightNowTime = time.strptime(rightNowString, "%Y-%m-%d %H:%M:%S")
        rightNowsolar = solarPosition(rightNowTime, self.latitude, self.longitude, self.stdmeridian, DSTFlag)
        rightNowbeta = rightNowsolar.altitudeAngle()
        thisHour = rightNow.tm_hour + rightNow.tm_min/60.0
        plt.plot([thisHour],[rightNowbeta],'b.',markersize=10.0)

        # show it
        plt.show()     

    def getCounty(self):
        # open the connection, note longitude must be -ve for west
        f = urllib.urlopen('http://labs.silverbiology.com/countylookup/lookup.php?cmd=findCounty&DecimalLatitude=%s&DecimalLongitude=%s' % (self.latitude, -self.longitude))
        # read the results
        s = f.read()
        # take out start and end curly brackets
        s2 = s[1:-1]
        # remove all in-string quotes
        s3 = s2.replace('"', '')
        # split into tokens
        s4 = s3.split(',')
        # create a list 
        entries = []
        # now populate it
        for sItem in s4:
            thisList = sItem.split(':')
            entries.append(thisList)
        # init a county variable
        county = ""
        # now get the county name
        for entry in entries:
            if entry[0] == 'County':
                county = entry[1]
        return county        
   
    def getWatchWarnings(self):
        # init line counter
        lineNum = 0
        # init a return value (list of watch/warnings)
        watchWarnings = []
        try:
            # open the connection to wunderground
            f = urllib.urlopen('http://www.wunderground.com/severe.asp')
            # read the results
            s = f.read()
        except:
            print "Couldn't read severe site"
            return watchWarnings
        # this is the title of the state box where warnings would be found
        sState='<a name="Oklahoma"></a>'
        # check if oklahoma is even in the entire contents
        if not sState in s:
            print "Didn't find Oklahoma in the severe list"
            return watchWarnings
        # Start reading lines, first create a string IO object
        buff = StringIO.StringIO(s)
        # read the first line to get things started
        line = buff.readline()
        lineNum += 1
        # then start looping over the string until we run out of lines
        while line:
            if line.strip() == sState:
                # we've found our state box, now let's skip the next two lines, since they are just box definitions
                dummy = buff.readline()
                lineNum += 1
                dummy = buff.readline()
                lineNum += 1
                # now we need to start processing the warnings.  These come in quadrature:
                # 1: a line with boxTitle in it specifying the watch/warning type
                # 2: a line that says warnList
                # 3: a line that contains a comma delimited list of these: <a href="SomeLinkPath.html">CountyOrLandmarkName</a>
                # 4: a </div> line
                lboxTitle = buff.readline()
                lineNum += 1
                while not 'Footer' in lboxTitle:
                    # read in relevant and dummy lines for this warn box
                    warnList = buff.readline()
                    lineNum += 1
                    warnLocations = buff.readline()
                    lineNum += 1
                    div      = buff.readline()
                    lineNum += 1
                    
                    # process the warning type into a useful parameter
                    ignore, thisWarnType = self.getWarnType(lboxTitle)
                    
                    # if we aren't ignoring it, do more stuff
                    if not ignore:
                        if self.thisCounty in warnLocations:
                            watchWarnings.append(thisWarnType)
                            #print watchWarnings
                    
                    # read another box title
                    lboxTitle = buff.readline()
                    lineNum += 1
                    if 'Footer' in lboxTitle:
                        break
                        
            # get the next line if it exists
            line = buff.readline()
            lineNum += 1
        
        return watchWarnings
            
    def getWarnType(self, str):
        # expects a line like:
        # <div class="boxTitle">WarningOrWatchType</div>
        # with 'Tornado Warning', 'Tornado Watch', 'Severe Thunderstorm Warning', or 'Severe Thunderstorm Watch'...any others are ignored
        if self.storms.sTornadoWarning in str:
            return False, self.storms.TornadoWarning
        elif self.storms.sTornadoWatch in str:
            return False, self.storms.TornadoWatch
        elif self.storms.sTstormWarning in str:
            return False, self.storms.TstormWarning
        elif self.storms.sTstormWatch in str:
            return False, self.storms.TstormWatch
        else:
            return True, self.storms.NoStorms
                    
    def main(self):
        gtk.main()

# main code that runs other program
if __name__ == "__main__":        
    Weather().main()
