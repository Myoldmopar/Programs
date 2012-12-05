#!/usr/bin/python

# dependencies:
#python-gobject maybe?
#python-gobject-dev maybe?
#gobject-introspection maybe?
#python-matplotlib (which depends on python and python-numpy)
#python-configobj (for config file)
# certainly some QT dependencies
# currently trying python-qt4

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
from solarPosition import solarPosition
import sys
from PyQt4 import QtGui, QtCore
import calendarPlot
import urllib

class Weather(object):
    
    oneTimeQTinit = True
    
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

        # plot solar profile for a different day
        self.menu_solar_anyday_item = gtk.MenuItem("Plot another day's solar")
        self.menu.append(self.menu_solar_anyday_item)
        self.menu_solar_anyday_item.show()
        self.menu_solar_anyday_item.connect("activate",self.plotSolarAnyDay)

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
        
        # issue a message
        os.system('zenity --info --text="Not yet implemented...for now just modify the config file: %s"' % (self.config_file_path))  
        
        # update any dynamic settings
        self.init_dynamicSettings_menu()
        
        # nothing?
        return
                
    def do_a_refresh(self, widget=None):
                
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
        
        # create an update string
        sIndicator = " %s%sF  %s%s " % (str(temp), self.degree_symbol, str(windspeed), arrow)
        
        # this will be used a few times here
        thistime = datetime.now()
                
        # update the menu item to say we have updated
        self.menu_update_item.set_label(thistime.strftime("Updated at: %Y-%b-%d %H:%M:%S"))
        
        # update the indicator label with new data
        self.ind.set_label(sIndicator)
        
        # send a notification message
        sNotify = "Temperature:\t%s\nWind Speed:\t%s\nWind Direction:\t%s" % (str(temp), str(windspeed), winddir)
        self.notification = Notify.Notification.new (self.locale_name + " Weather Updated", sNotify, '') 
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
        
    def plotSolarAnyDay(self, widget):
        
        # only create the QTapp runtime once
        if self.oneTimeQTinit == True:
            self.app = QtGui.QApplication(sys.argv)
            self.oneTimeQTinit = False

        # create and show the calendar dialog
        gui = calendarPlot.CalendarPlot()
        gui.show()
        
        # start the message loop
        self.app.exec_()
        
        # if the user clicked OK, show the plot
        if gui.result == "OK":
            thisDay = gui.cal.selectedDate()
            # note that the fourth item % item here is actually escaped to leave a percent symbol
            thisDayString = "%s-%s-%s %%s:00:00" % (thisDay.year(), thisDay.month(), thisDay.day())
            plotDayString = '%s-%s-%s' % (thisDay.year(), thisDay.month(), thisDay.day())
            DST = self.getDST(thisDay.year(), thisDay.month(), thisDay.day())
            self.plotSolar(thisDayString, plotDayString, DST)
        
    def plotSolar(self, singleDayString, plotDateString, DSTFlag):
        
        #singleDayString should be of the form "YEAR-MONTH-DATE %s:00:00" so that the %s can be swept over 24 hours in a loop
        #plotDateString is just a label for the top of the plot
        
        # calculate the altitude angle for each hour (could do each half hour or whatever)
        altitudes = []
        for hour in range(0,24):
            print hour
            thisTime = time.strptime(singleDayString % str(hour), "%Y-%m-%d %H:%M:%S")   
            solar = solarPosition(thisTime, self.latitude, self.longitude, self.stdmeridian, DSTFlag)
            beta = solar.altitudeAngle()
            altitudes.append(beta)
        print altitudes

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
            
    def main(self):
        gtk.main()

if __name__ == "__main__":        
    Weather().main()
