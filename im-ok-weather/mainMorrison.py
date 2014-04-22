#!/usr/bin/python

# dependencies:
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

#http://www.wunderground.com/cgi-bin/findweather/hdfForecast?query=morrison%2C+co
#<meta name="og:title" content="Morrison, CO | 79.5&deg; | Scattered Clouds" />
#<span id="windCompass" class="pwsrt" pwsid="KOKSTILL4" pwssetobject="winddir" pwsunit="english" pwsvariable="winddir" english="" metric="" value="332"></span>
#       360=due north, 270=due west, 180=due south, 90=due east
#       therefore:  [337.5, 22.5) = N
#                   [22.5, 67.5)  = NE
#                   [67.5, 112.5) = E
#                   [112.5, 157.5) = SE
#                   [157.5, 202.5) = S
#                   [202.5, 247.5) = SW
#                   [247.5, 292.5) = W
#                   [292.5, 337.5) = NW
#<span id="windCompassSpeed" class="pwsrt" pwsid="KOKSTILL4" pwsunit="english" pwsvariable="windspeedmph" english="" metric="">5.0</span>

# a class with storm enumeration and a few workers

class Storms():
    
    def __init__(self):
        self.NoStorms        = 0
        self.TornadoWarning  = 1
        self.sTornadoWarning = 'Tornado Warning'
        self.TornadoWatch    = 2
        self.sTornadoWatch   = 'Tornado Watch'
        self.TstormWarning   = 3
        self.sTstormWarning  = 'Severe Thunderstorm Warning'
        self.TstormWatch     = 4
        self.sTstormWatch    = 'Severe Thunderstorm Watch'
	self.WindAdvisory    = 5
	self.sWindAdvisory   = 'Wind Advisory'
    
    def getCounty(self, latitude, longitude):
        # open the connection, note longitude must be -ve for west
        try:
            f = urllib.urlopen('http://labs.silverbiology.com/countylookup/lookup.php?cmd=findCounty&DecimalLatitude=%s&DecimalLongitude=%s' % (latitude, longitude))
            # read the results
            s = f.read()
        except:
            return 'CouldntConnectCounty'
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
   
    def getWatchWarnings(self, county):
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
        sState='<a name="Colorado"></a>'
        # check if the state is even in the entire contents
        if not sState in s:
            print "Didn't find Colorado in the severe list"
            return watchWarnings
        # Start reading lines, first create a string IO object
        buff = StringIO.StringIO(s)
        # read the first line to get things started
        line = buff.readline()
        lineNum += 1
        # then start looping over the string until we run out of lines
        while line:
            if line.strip() == sState:
                
		# we've found our state box, here's the way it's structured right now:
		
		# <a name="Colorado"></a>
		# <dl class="accordion wui-accordion" data-accordion>
		# <dd>
		# <a href="#group-5">Colorado</a>
		# <div id="group-5" class="content">
		# <strong>Wind Advisory</strong>
		# <ul class="inline-list">
		# <li><a href="/US/CO/.html"></a></li>
		# <li><a href="/US/CO/.html"></a></li>
		# <li><a href="/US/CO/011.html">Central Gunnison and Uncompahgre River Basin</a></li>
		# <li><a href="/US/CO/002.html">Central Yampa River Basin</a></li>
		# <li><a href="/US/CO/090.html">Yuma County</a></li>
		# </ul>
		# <strong>Fire Weather Warning</strong>
		# <ul class="inline-list">
		# <li><a href="/US/CO/.html"></a></li>
		# <li><a href="/US/CO/.html"></a></li>
		# <li><a href="/US/CO/089.html">Crowley County</a></li>
		# <li><a href="/US/CO/091.html">Kit Carson County</a></li>
		# <li><a href="/US/CO/090.html">Yuma County</a></li>
		# </ul>
		# </div>  -- STOP HERE
		
		# so we need to: 
		# 1) ignore the accordian, dd, a href, and div id lines. (4)
		dummy = buff.readline()
                lineNum += 1
                dummy = buff.readline()
                lineNum += 1
                dummy = buff.readline()
                lineNum += 1
                dummy = buff.readline()
                lineNum += 1
                
		# 2) start reading each group of advisories
		lineTrimmed = buff.readline()
		lineNum += 1
		
                counter = 0
		while not '</div>' in lineTrimmed:
		    
		    # increment the counters to avoid continuing to read infinitely
		    counter += 1
		    if counter >= 10000:
			print "Hit max watch/warning counters, quitting looking"
			return watchWarnings
		
		    if '<strong>' in lineTrimmed:
			
			# process the warning type into a useful parameter
			ignore, thisWarnType = self.getWarnType(lineTrimmed)
                    
			# read the next line because it is just the UI command
			lineTrimmed = buff.readline()
			lineNum += 1
			
			# then start reading the county lines
			while True:
			    
			    lineTrimmed = buff.readline()
			    lineNum += 1
			
			    if '</ul>' in lineTrimmed:
				break
			
			    if not ignore:
				if county in lineTrimmed:
				    watchWarnings.append(thisWarnType)
				    break
				    
		    else: # strong *not* in lineTrimmed
			
			# just read another line
			lineTrimmed = buff.readline()
			lineNum += 1
			
            # get the next line if it exists
            line = buff.readline()
            lineNum += 1
	    
	    # end the line reading if we hit the end of the html
	    if '</html>' in line:
		break
        
	#TODO: Verify that storms are read in properly
        #watchWarnings.append(self.TstormWarning)
        return watchWarnings
            
    def getWarnType(self, str):
        # expects a line like:
        # <strong>Wind Advisory</strong>
        # with 'Tornado Warning', 'Tornado Watch', 'Severe Thunderstorm Warning', or 'Severe Thunderstorm Watch'...any others are ignored
        if self.sTornadoWarning in str:
            return False, self.TornadoWarning
        elif self.sTornadoWatch in str:
            return False, self.TornadoWatch
        elif self.sTstormWarning in str:
            return False, self.TstormWarning
        elif self.sTstormWatch in str:
            return False, self.TstormWatch
	elif self.sWindAdvisory in str:
	    return False, self.WindAdvisory
        else:
            return True, self.NoStorms
   
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

# plotting operation
class plotting():
    
    def __init__(self):
        self.stdmeridian = 105
        self.plotX = [] # maybe remove since init'd in setLocation
        self.plotY = []
        self.degree_symbol = unichr(176)
        
    def setLocation(self, latitude, longitude):
        self.plotX = []
        self.plotY = []
        self.latitude = latitude
        self.longitude = longitude
        
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
        elif year == 2013:
            if month == 3 and date >= 10:
                retVal = True
            elif month > 3 and month < 11:
                retVal = True
            elif month == 11 and date < 3:
                retVal = True
        elif year == 2014:
            if month == 3 and date >= 9:
                retVal = True
            elif month > 3 and month < 11:
                retVal = True
            elif month == 11 and date < 2:
                retVal = True
        elif year == 2015:
            if month == 3 and date >= 8:
                retVal = True
            elif month > 3 and month < 11:
                retVal = True
            elif month == 11 and date < 1:
                retVal = True
        elif year == 2016:
            if month == 3 and date >= 13:
                retVal = True
            elif month > 3 and month < 11:
                retVal = True
            elif month == 11 and date < 6:
                retVal = True
        else:
            print "DST not yet implemented for years later than 2016...defaulting to not DST"
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

# the full weather program class
class Weather(object):
    
    def destroy(self, widget):
        gtk.main_quit()

    def __init__(self):
        
        # ---------------------- BEGIN ORDER-INDEPENDENT INITIALIZATION ----------------------- #
        # init some global "constants"
        self.appname = "im-ok-weather"
        self.unknown = "??"
        self.locale_name = "Morrison"
        self.url = "http://www.wunderground.com/cgi-bin/findweather/hdfForecast?query=morrison%2C+co"
        self.degree_symbol = unichr(176)
        self.config_file_path = os.getenv("HOME") + "/.config/" + self.appname
        self.stdmeridian = 105
        self.storms = Storms()
        
	# morrison
        self.latitude = 39.651667
        self.longitude = -105.190278
	
	# cheyenne county hack
	#self.latitude = 38.818532
	#self.longitude = -102.593761
	
        self.update_interval_ms = 300000 # 3e5 ms = 300 seconds = 5 minutes = mesonet update frequency
        
        self.plotter = plotting()
        self.plotter.setLocation(self.latitude, -self.longitude)
        self.county = self.storms.getCounty(self.latitude, self.longitude)
                
        # init the notification system
        Notify.init(self.appname)
        try:
            self.notification = Notify.Notification.new('', '', '') 
            self.notifs = True
        except:
            self.notifs = False
        
        # init the gtk menu -- need to wait until we have 
        self.init_menu()
        
        # init the app-indicator ability
        self.ind = appindicator.Indicator("im-ok-weather","", appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_menu(self.menu)
                                    
        # do a refresh once initially
        self.do_a_refresh()

        # then set up the timer
        self.timer = gobject.timeout_add(self.update_interval_ms, self.do_a_refresh)

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
        self.menu_plot_item.connect("activate", self.plotter.plot)

        # plot solar profile for today
        self.menu_solar_today_item = gtk.MenuItem("Plot today's solar")
        self.menu.append(self.menu_solar_today_item)
        self.menu_solar_today_item.show()
        self.menu_solar_today_item.connect("activate", self.plotter.plotSolarToday)

        # separator for cleanliness
        self.menu_sep_item = gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item)
        self.menu_sep_item.show()
         
        # updated time item
        self.menu_update_item = gtk.MenuItem("Initializing...")
        self.menu.append(self.menu_update_item)
        self.menu_update_item.show()
        
        # separator for cleanliness
        self.menu_sep_item3 = gtk.SeparatorMenuItem()
        self.menu.append(self.menu_sep_item3)
        self.menu_sep_item3.show()        
        
        # quit item
        self.menu_quit_item = gtk.MenuItem("Quit")
        self.menu.append(self.menu_quit_item)
        self.menu_quit_item.show()
        self.menu_quit_item.connect("activate", self.destroy)

    def do_a_refresh(self, widget=None):

        # init line counter
        lineNum = 0
       
        # flag strings
        flagTemp = 'pwsvariable="tempf"'
        flagWindSpeed = 'pwsvariable="windspeedmph"'
        flagWindDir = 'pwsvariable="winddir"'
        flagEnd = '</html>'
        
	preferredLocation = 'KCOLAKEW19'
	preferredTemp = None
	preferredSpeed = None
	preferredDir = None
	preferredTempFound = False
	preferredSpeedFound = False
	preferredDirFound = False
	
        # init return values
        temp = self.unknown
        windspeed = self.unknown
        winddir = self.unknown
        arrow = ""
       
        # try to read the data
        try:
            # open the connection to wunderground
            f = urllib.urlopen(self.url)
            # read the results
            s = f.read()
        except:
            # just leave the return values as init'd
            print "Couldn't read weather site"
            s = ""

        # only start parsing if we actually read something
        if s:
            try:
            
                # Start reading lines, first create a string IO object
                buff = StringIO.StringIO(s)
                
                # read the first line to get things started
                line = buff.readline()
                lineNum += 1
                
                # then start looping over the string until we run out of lines
                while line:
                    
		    if flagTemp in line:
			if preferredTempFound:
			    pass
			else:
			    sTemp = line.split('=')[-1].split('"')[1] #line.split('|')[1].split('&')[0].strip()
			    fTemp = float(sTemp)
			    temp = int(fTemp)
			    if preferredLocation in line:
				preferredTemp = temp
				preferredTempFound = True
                        
                    elif flagWindSpeed in line:
			if preferredSpeedFound:
			    pass
			else:
			    sWind = line.split('=')[-1].split('"')[1]
			    fWind = float(sWind)
			    windspeed = int(fWind)
			    if preferredLocation in line:
				preferredSpeed = windspeed
				preferredSpeedFound = True
                                                
                    elif flagWindDir in line:
			if preferredDirFound:
			    pass
			else:
			    winddir = line.split('=')[-1].split('"')[1]
			    arrow = ""
			    try:
				d = float(double)
				arrow = self.get_arrow_from_compass(winddir)
			    except:
				arrow = self.get_arrow_from_compass_dirstring(winddir)                       
			    if preferredLocation in line:
				preferredDir = arrow
				preferredDirFound = True
                        			
                    elif flagEnd in line:
			break
                                
                    # get the next line if it exists
                    line = buff.readline()
                    lineNum += 1
            
            except Exception as e:
            
		print "Exception in do_a_refresh..."
		print line
		print e
                
	# take the "preferred location info if it existed"
	if preferredDirFound:
	    temp = preferredTemp
	    #print "using preferredTemp"
	if preferredDirFound:
	    windspeed = preferredSpeed
	    #print "using preferredSpeed"
	if preferredDirFound:
	    arrow = preferredDir
	    #print "using preferredDir"
	    
        # create an update string
        sIndicator = " %s%sF  %s%s " % (str(temp), self.degree_symbol, str(windspeed), arrow)
        
        # this will be used a few times here
        thistime = datetime.now()
                
        # update the menu item to say we have updated
        self.menu_update_item.set_label(thistime.strftime("Updated at: %Y-%b-%d %H:%M:%S"))
        
        # check for severe weather
        theseWarnings = self.storms.getWatchWarnings(self.county)
        #print theseWarnings 
                 
        # update the indicator label with new data
        self.ind.set_label(sIndicator)
        
        # for some reason, the direction appears to come in as either a numeric angle *or* a direction name......
        try:
            thisDirName = self.get_arrowName_from_compass(winddir)
        except:
            thisDirName = winddir
            
        # send a notification message
        sNotify = "Temperature:\t%s\nWind Speed:\t%s\nWind Direction:\t%s" % (str(temp), str(windspeed), thisDirName)
        if self.notifs:
            if not theseWarnings:
                self.notification.update(self.locale_name + " Weather Updated", sNotify, '') 
                self.notification.show()
            elif self.storms.TornadoWarning in theseWarnings:
                self.notification.update(self.locale_name + " Weather Updated", sNotify+"\n ** TORNADO WARNING!", '') 
                self.notification.show()
            elif self.storms.TornadoWatch in theseWarnings:
                self.notification.update(self.locale_name + " Weather Updated", sNotify+"\n ** Tornado Watch!", '') 
                self.notification.show()
            elif self.storms.TstormWarning in theseWarnings:
                self.notification.update(self.locale_name + " Weather Updated", sNotify+"\n ** Severe Thunderstorm Warning!", '') 
                self.notification.show()
            elif self.storms.TstormWatch in theseWarnings:
                self.notification.update(self.locale_name + " Weather Updated", sNotify+"\n ** Severe Thunderstorm Watch", '') 
                self.notification.show()
	    elif self.storms.WindAdvisory in theseWarnings:
                self.notification.update(self.locale_name + " Weather Updated", sNotify+"\n ** Wind Advisory", '') 
                self.notification.show()
            else:
                self.notification.update(self.locale_name + " Weather Updated", sNotify+"\n ** Unkown watch/warning state", '') 
                self.notification.show()
                
        # store the current time and temperature for plotting
        thistime_num = matplotlib.dates.date2num(thistime)
        self.plotter.plotX.append(thistime_num)
        self.plotter.plotY.append(temp)
                
        # callback return value, so that gobject knows it can continue cycling
        return True
          
    def get_arrow_from_compass(self, angle):
        angle = int(angle)
        if angle < 22.5 or angle >= 337.5:
            arrow = u"\u2193" # downwards pointing arrow
        elif angle < 112.5 and angle >= 67.5:
            arrow = u"\u2190" # leftwards pointing arrow
        elif angle < 202.5 and angle >= 157.5:
            arrow = u"\u2191" # upwards pointing arrow
        elif angle < 292.5 and angle >= 247.5:
            arrow = u"\u2192" # rightwards pointing arrow
        elif angle < 67.5 and angle >= 22.5:
            arrow = u"\u2199" # southwest pointing arrow
        elif angle < 337.5 and angle >= 292.5:
            arrow = u"\u2198" # southeast pointing arrow
        elif angle < 157.5 and angle >= 112.5:
            arrow = u"\u2196" # northwest pointing arrow
        elif angle < 247.5 and angle >= 202.5:
            arrow = u"\u2197" # northeast pointing arrow
        else:
            print " Oops...bad wind direction passed to self.get_arrow_from_compass(), dir = " + dir
        #print "Direction = %s, Arrow = %s" % (angle, arrow)
        return arrow            

    def get_arrowName_from_compass(self, angle):
        angle = int(angle)
        if angle < 22.5 or angle >= 337.5:
            arrow = "North" # downwards pointing arrow
        elif angle < 112.5 and angle >= 67.5:
            arrow = "East" # leftwards pointing arrow
        elif angle < 202.5 and angle >= 157.5:
            arrow = "South" # upwards pointing arrow
        elif angle < 292.5 and angle >= 247.5:
            arrow = "West" # rightwards pointing arrow
        elif angle < 67.5 and angle >= 22.5:
            arrow = "Northeast" # southwest pointing arrow
        elif angle < 337.5 and angle >= 292.5:
            arrow = "Northwest" # southeast pointing arrow
        elif angle < 157.5 and angle >= 112.5:
            arrow = "Southeast" # northwest pointing arrow
        elif angle < 247.5 and angle >= 202.5:
            arrow = "Southwest" # northeast pointing arrow
        else:
            print " Oops...bad wind direction passed to self.get_arrow_from_compass(), dir = " + dir
        #print "Direction = %s, Arrow = %s" % (angle, arrow)
        return arrow   
          
    def get_arrow_from_compass_dirstring(self, sAngle):
        sAngle = sAngle.upper()
        if sAngle in ["N", "NORTH"]:
            arrow = u"\u2193" # downwards pointing arrow
        elif sAngle in ["E", "EAST"]:
            arrow = u"\u2190" # leftwards pointing arrow
        elif sAngle in ["S", "SOUTH"]:
            arrow = u"\u2191" # upwards pointing arrow
        elif sAngle in ["W", "WEST"]:
            arrow = u"\u2192" # rightwards pointing arrow
        elif sAngle in ["NNE", "NE", "ENE"]:
            arrow = u"\u2199" # southwest pointing arrow
        elif sAngle in ["NNW", "NW", "WNW"]:
            arrow = u"\u2198" # southeast pointing arrow
        elif sAngle in ["SSE", "SE", "ESE"]:
            arrow = u"\u2196" # northwest pointing arrow
        elif sAngle in ["SSW", "SW", "WSW"]:
            arrow = u"\u2197" # northeast pointing arrow
        else:
            print " Oops...bad wind direction passed to self.get_arrow_from_compass_dirstring(), dir = " + dir
        #print "Direction = %s, Arrow = %s" % (sAngle, arrow)
        return arrow            	  
	  
    def main(self):
        gtk.main()

# main code that runs other program
if __name__ == "__main__":        
    Weather().main()
