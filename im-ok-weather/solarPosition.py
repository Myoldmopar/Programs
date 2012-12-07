#!/usr/bin/env python

import math
import time
import datetime

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
    
    def generateSunData(self, latitude, longitude, myBaseDate):
        pass
        dummy="""
        #Dim myDate As DateTime
        #Dim StandardMeridian As Single = 90
        #Dim LocalTimeValues(23) As DateTime
        #Dim BetaValues(23) As Single
        #Dim RightNowTime(0) As DateTime
        #Dim RightNowBeta(0) As Single

        #For HourCounter As Integer = 0 To 24
            #If HourCounter <= 23 Then
                #myDate = New DateTime(MyBaseDate.Year, MyBaseDate.Month, MyBaseDate.Day, HourCounter, 0, 0)
                #LocalTimeValues(HourCounter) = myDate
            #Else
                #myDate = MyBaseDate
                #RightNowTime(0) = myDate
            #End If

            #Dim myDayofYear As Integer = myDate.DayOfYear

            #Dim DSTStartDate As New DateTime(2009, 3, 8, 2, 0, 0)  '2009
            #Dim DSTStartDay As Integer = DSTStartDate.DayOfYear
            #Dim DSTEndDate As New DateTime(2009, 11, 1, 2, 0, 0) '2009
            #Dim DSTEndday As Integer = DSTEndDate.DayOfYear
            #Dim DSTOnOff As Boolean = False
            #If myDayofYear >= DSTStartDay AndAlso myDayofYear < DSTEndday Then DSTOnOff = True

            #If DSTOnOff Then myDate = TruncateOneHour(myDate)

            #Dim LocalCivilHours As Integer = myDate.Hour
            #Dim LocalCivilMinutes As Integer = myDate.Minute
            #Dim LocalCivilSeconds As Integer = myDate.Second
            #Dim LocalCivilTime As Double = LocalCivilHours + LocalCivilMinutes / 60 + LocalCivilSeconds / 60 / 60

            #Dim Beta As Double = SOLALT(latitude, longitude, StandardMeridian, LocalCivilTime, myDate)
            #If HourCounter <= 23 Then
                #BetaValues(HourCounter) = CSng(Beta)
            #Else
                #RightNowBeta(0) = CSng(Beta)
            #End If
        #Next

        #Dim RiseSetTimes() As DateTime = InterpRiseSet(LocalTimeValues, BetaValues)

        #Dim PlotSeriesCollection As New Collection()

        #PlotSeriesCollection.Add(LocalTimeValues)
        #PlotSeriesCollection.Add(BetaValues)
        #PlotSeriesCollection.Add(RightNowTime)
        #PlotSeriesCollection.Add(RightNowBeta)

        #Dim PlotResults As New PlotForm
        #With PlotResults
            #.MakeAPlot(PlotSeriesCollection, Form1.TempOrSolar.Solar, RiseSetTimes)
            #.Text = "Solar position throughout the day"
            #.ShowDialog()
            #.Dispose()
        #End With
        #PlotSeriesCollection = Nothing"""

    def interpRiseSet(self, timeArray, valArray):
        pass
        dummy = """
        #Dim StoredValue As Single
        #Dim NewValue As Single = valArray(0)
        #Dim TimeIndexJustAfterSunRise As Integer
        #Dim TimeIndexJustAfterSunSet As Integer
        #Dim SunRiseFound As Boolean = False
        #Dim SunSetFound As Boolean = False

        #For TimeCounter As Integer = 0 To timeArray.GetUpperBound(0) - 1 'skip the very first and last values
            #StoredValue = NewValue
            #If TimeCounter = 0 Then Continue For
            #NewValue = valArray(TimeCounter)
            #If Not SunRiseFound Then
                #If StoredValue < 0 And NewValue >= 0 Then
                    #SunRiseFound = True
                    #TimeIndexJustAfterSunRise = TimeCounter
                    #Continue For
                #End If
            #End If
            #If (SunRiseFound) AndAlso (Not SunSetFound) Then
                #If StoredValue > 0 And NewValue <= 0 Then
                    #SunSetFound = True
                    #TimeIndexJustAfterSunSet = TimeCounter
                    #Exit For
                #End If
            #End If
        #Next

        #If (Not SunRiseFound) Or (Not SunSetFound) Then Return Nothing

        #Dim TimeJustBeforeSunRise As Double = timeArray(TimeIndexJustAfterSunRise - 1).ToBinary
        #Dim TimeJustAfterSunRise As Double = timeArray(TimeIndexJustAfterSunRise).ToBinary
        #Dim TimeJustBeforeSunSet As Double = timeArray(TimeIndexJustAfterSunSet - 1).ToBinary
        #Dim TimeJustAfterSunSet As Double = timeArray(TimeIndexJustAfterSunSet).ToBinary

        #Dim ValJustBeforeSunRise As Double = valArray(TimeIndexJustAfterSunRise - 1)
        #Dim ValJustAfterSunRise As Double = valArray(TimeIndexJustAfterSunRise)
        #Dim ValJustBeforeSunSet As Double = valArray(TimeIndexJustAfterSunSet - 1)
        #Dim ValJustAfterSunSet As Double = valArray(TimeIndexJustAfterSunSet)

        #Dim SunRiseVal As Double = -1
        #Dim SunSetVal As Double = -1

        #Dim SunRiseTimeVal As Double
        #Dim SunSetTimeVal As Double

        #SunRiseTimeVal = ((SunRiseVal - ValJustBeforeSunRise) / (ValJustAfterSunRise - ValJustBeforeSunRise)) * (TimeJustAfterSunRise - TimeJustBeforeSunRise) + TimeJustBeforeSunRise
        #SunSetTimeVal = ((SunSetVal - ValJustBeforeSunSet) / (ValJustAfterSunSet - ValJustBeforeSunSet)) * (TimeJustAfterSunSet - TimeJustBeforeSunSet) + TimeJustBeforeSunSet

        #Dim ReturnData(1) As DateTime
        #ReturnData(0) = DateTime.FromBinary(CLng(SunRiseTimeVal))
        #ReturnData(1) = DateTime.FromBinary(CLng(SunSetTimeVal))

        #Return ReturnData"""

    def truncateOneHour(self, iDate):
        pass
        dummy="""
        #Dim Year As Integer = idate.Year
        #Dim Month As Integer = idate.Month
        #Dim Day As Integer = idate.Day
        #Dim Hour As Integer = idate.Hour
        #Dim Minute As Integer = idate.Minute
        #Dim Second As Integer = idate.Second

        #Dim NewHour As Integer = Hour - 1
        #Dim NewDay As Integer = Day
        #Dim NewMonth As Integer = Month
        #Dim NewYear As Integer = Year

        #If NewHour < 0 Then
            #NewHour += 24
            #NewDay = Day - 1
            #If NewDay < 1 Then
                #If Month = 1 Then
                    #NewDay += DateTime.DaysInMonth(Year, 12)
                #Else
                    #NewDay += DateTime.DaysInMonth(Year, Month - 1)
                #End If
                #NewMonth = Month - 1
                #If NewMonth < 1 Then
                    #NewMonth += 12
                    #NewYear = Year - 1
                #End If
            #End If
        #End If

        #Return New DateTime(NewYear, NewMonth, NewDay, NewHour, Minute, Second)"""

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
        #print string


        
