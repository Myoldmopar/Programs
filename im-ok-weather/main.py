#!/usr/bin/python

# dependencies:
#python-gobject maybe?
#python-gobject-dev maybe?
#gobject-introspection maybe?
#python-matplotlib (which depends on python and python-numpy)
#python-configobj (for config file)

from gi.repository import Notify
import re
import urllib2
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
import urllib
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

class settingsWindow(gtk.Window):
    
    def __init__(self):
        gtk.Window.__init__(self) 
        self.set_title("Update Settings")
        
        self.set_border_width(10)
        self.set_modal(True)
        meso_site_store = gtk.ListStore(str, str)
        meso_site_store.append(['STIL', 'Stillwater'])
        meso_site_store.append(['PAWN', 'Pawnee'])
        meso_site_store.append(['CARL', 'Lake Carl Blackwell'])
        
        meso_site_combo = gtk.ComboBox(model=meso_site_store)
        meso_site_combo.connect("changed", self.on_name_combo_changed)
        #meso_site_combo.set_entry_text_column(0)
        
        cell = gtk.CellRendererText()
        meso_site_combo.pack_start(cell, True)
        meso_site_combo.add_attribute(cell, "text", 1)
        
        btnOK = gtk.Button(stock = gtk.STOCK_OK)
        btnOK.connect("clicked", self.onOK)
        btnCancel = gtk.Button(stock = gtk.STOCK_CANCEL)
        btnCancel.connect("clicked", self.onCancel)
        
        hbox = gtk.HBox(spacing=6)
        hbox.pack_start(btnOK)
        hbox.pack_start(btnCancel)
                
        vbox = gtk.VBox(spacing=6)       
        vbox.pack_start(meso_site_combo, False, False, 0)
        vbox.pack_start(hbox, False, False, 0) 
        
        self.add(vbox)
        
        self.applyChanges = False

    def on_name_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            self.ID = model[tree_iter][0]
            print "Selected: ID=%s" % (self.ID)
        else:
            entry = combo.get_child()
            print "Entered: %s" % entry.get_text()

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
        
        # init some global "constants"
        self.appname = "im-ok-weather"
        self.unknown = "??"
        self.url = "http://www.mesonet.org/data/public/mesonet/current/current.csv.txt"
        self.degree_symbol = unichr(176)
        self.config_file_path = os.getenv("HOME") + "/.config/" + self.appname
        
        # init configurable parameters
        self.update_interval_ms = 300000 # 3e5 ms = 300 seconds = 5 minutes = mesonet update frequency
        self.mesonet_location_tag = 'STIL'
        self.latitude = 36.12
        self.longitude = 97.07 
        self.stdmeridian = 90
        
        # derived parameters based on configurable parameters
        self.county = self.getCounty()
                
        # init locale name (dynamically derived from configuration)...just set to Oklahoma initially
        self.locale_name = "Oklahoma"
        
        # other initialization
        self.storms = StormTypes()
        
        # override default configuration with saved data
        # FIXME: Allow newer versions of the config file to run without crashing after the upgrade
        #self.read_config_file()
        
        # flush output config...not necessary except to create a one-time init file...
        # FIXME: Allow newer versions of the config file to run without crashing after the upgrade
        #self.write_config_file()
        
        # init other global variables
        self.plotX = []
        self.plotY = []
        
        # init the notification system
        Notify.init(self.appname)
        self.notification = Notify.Notification.new('', '', '') 
        
        # initi the gtk menu
        self.init_menu()
        
        # init the app-indicator ability
        self.ind = appindicator.Indicator("im-ok-weather","", appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_menu(self.menu)
        
        # do a refresh once initially
        self.do_a_refresh()
        
        # then set up the timer
        self.timer = gobject.timeout_add(self.update_interval_ms, self.do_a_refresh)

    def read_config_file(self):
        if not os.path.exists(self.config_file_path):
            return          
        config = ConfigObj(self.config_file_path)
        self.update_interval_ms = int(config['update_interval_ms'])
        self.mesonet_location_tag = config['mesonet_location_tag']
        self.latitude = float(config['latitude']) 
        self.longitude = float(config['longitude'])    
        self.stdmeridian = float(config['stdmeridian']) 
        
    def write_config_file(self):
        config = ConfigObj(self.config_file_path)
        config['update_interval_ms'] = self.update_interval_ms
        config['mesonet_location_tag'] = self.mesonet_location_tag
        config['latitude'] = self.latitude
        config['longitude'] = self.longitude
        config['stdmeridian'] = self.stdmeridian
        config.write()
        
    def init_menu(self):
        
        # create a gtkMenu for the appindicator
        self.menu = gtk.Menu()
                
        # force a refresh item
        self.menu_force_item = gtk.MenuItem("Refresh now")
        self.menu.append(self.menu_force_item)
        self.menu_force_item.show()
        self.menu_force_item.connect("activate",self.do_a_refresh)

        # plot history
        self.menu_plot_item = gtk.MenuItem("Plot history")
        self.menu.append(self.menu_plot_item)
        self.menu_plot_item.show()
        self.menu_plot_item.connect("activate",self.plot)

        # plot solar profile for today
        self.menu_solar_today_item = gtk.MenuItem("Plot today's solar")
        self.menu.append(self.menu_solar_today_item)
        self.menu_solar_today_item.show()
        self.menu_solar_today_item.connect("activate",self.plotSolarToday)

        # separator for cleanliness
        self.menu_sep_item = gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item)
        self.menu_sep_item.show()
        
        # current location item
        self.menu_cur_item = gtk.MenuItem("Current location keyword: %s" % self.mesonet_location_tag)
        self.menu.append(self.menu_cur_item)
        self.menu_cur_item.show()
        
        # current interval item
        self.menu_curtime_item = gtk.MenuItem("Current update interval: %sms" % self.update_interval_ms)
        self.menu.append(self.menu_curtime_item)
        self.menu_curtime_item.show()
        
        # updated time item
        self.menu_update_item = gtk.MenuItem("Initializing...")
        self.menu.append(self.menu_update_item)
        self.menu_update_item.show()
        
        # separator for cleanliness
        self.menu_sep_item2 = gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item2)
        self.menu_sep_item2.show()
        
        # item to update settings
        self.menu_settings_item = gtk.MenuItem("Update settings...")
        self.menu.append(self.menu_settings_item)
        self.menu_settings_item.show()
        self.menu_settings_item.connect("activate",self.update_settings)
        
        # separator for cleanliness
        self.menu_sep_item3 = gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item3)
        self.menu_sep_item3.show()        
        
        # quit item
        self.menu_quit_item = gtk.MenuItem("Quit")
        self.menu.append(self.menu_quit_item)
        self.menu_quit_item.show()
        self.menu_quit_item.connect("activate",self.destroy)

    def init_dynamicSettings_menu(self):
        
        # current location item
        self.menu_cur_item.set_label("Current location keyword: %s" % self.mesonet_location_tag)
        # current interval item
        self.menu_curtime_item.set_label("Current update interval: %sms" % self.update_interval_ms)

    def update_settings(self, widget):
        
        win = settingsWindow()
        win.show_all()
        win.connect("hide", self.handleClose)
        # issue a message
        #os.system('zenity --info --text="Not yet implemented...for now just modify the config file: %s"' % (self.config_file_path))  
        
        # update any dynamic settings
        self.init_dynamicSettings_menu()
        
        # nothing?
        return

    def handleClose(self, widget):
        print "it closed"
                
    def do_a_refresh(self, widget=None):
                
        try:        
            
            # open the site, and read the results into a variable
            f = urllib2.urlopen(self.url)
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
