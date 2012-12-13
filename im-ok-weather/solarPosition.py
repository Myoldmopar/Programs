#!/usr/bin/env python

import math
#import time
#import datetime

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


        
