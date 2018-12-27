###################################################################
# Weather Alert - Poll for alerts from weatherunderground and alert to HA
# Written By : Chip Cox  20JAN2017
#                 
#    V0.01.1 21JAN2017 - updated to handle european data
#    V0.01.2 21JAN2017 - added configuration options 
#    V0.01.3 29MAR2017 - Added support for AppDaemon HADashboards Beta 3
#
###################################################################
#
# Use:
#   Add the following lines to your appDaemon config file
#     [weatherAlert]
#     module=weatherAlert
#     class=weatheralert
#     alerts = {"HEA","TOR"}
#     key = "your weather underground key"
#   * location={"city":"your city","state":"your state"}  or {"zmw":"your zmw"}`
#   * frequency=minutes between checks   ( Defaults to 15 min )
#   * title=title of persistent notification window
#   * dash_dir = /home/pi/appdaemon_dashboard/appdaemon/conf/custom_css/notices/   - directory to where alert pages should be placed
#
#   * entries are  optional
#
#     location can be expressed as a dictionary containing the following:
#                                    {"city":"your city", "state":"your state"}
#                                    {"zip":"your zip code"}
#                                    {"Country":"Your country name","city":"Your city"}
#                                    if location is not in the config file, it defaults to your HomeAssistant Latitude/Longitude
#     
#   Possible values for alerts are : type	Translated
#                                    HUR	Hurricane Local Statement
#                                    TOR	Tornado Warning
#                                    TOW	Tornado Watch
#                                    WRN	Severe Thunderstorm Warning
#                                    SEW	Severe Thunderstorm Watch
#                                    WIN	Winter Weather Advisory
#                                    FLO	Flood Warning
#                                    WAT	Flood Watch / Statement
#                                    WND	High Wind Advisory
#                                    SVR	Severe Weather Statement
#                                    HEA	Heat Advisory
#                                    FOG	Dense Fog Advisory
#                                    SPE	Special Weather Statement
#                                    FIR	Fire Weather Advisory
#                                    VOL	Volcanic Activity Statement
#                                    HWW	Hurricane Wind Warning
#                                    REC	Record Set
#                                    REP	Public Reports
#                                    PUB	Public Information Statement
#
#  dash_dir - currently this needs to be in a folder under your custom_css directory.
#
#  If you are using the following speach apps in appdaemon
#  sound - by Rene Tode - https://community.home-assistant.io/t/let-appdaemon-speak-without-tts-and-mediaplayer-in-hass/8058
#  speak - by Chip Cox - https://github.com/turboc1208/AppDaemonApps/blob/master/speak.py
#
#  weatherAlert will recognize them and send alerts to your speakers as well
#  as the persistent_notifications.
#
##################################################################################
#
# Visit the weatherunderground at the following link for more information about this API
# https://www.wunderground.com/weather/api/d/docs?d=data/alerts
##################################################################################
import appdaemon.plugins.hass.hassapi as hass
import datetime
import time
import requests
from requests.auth import HTTPDigestAuth
import json
import os
         
class weatheralert(hass.Hass):

  def initialize(self):
    self.LOGLEVEL="DEBUG"
    self.alertlog={}
    self.log("Weather Alert App")
    self.source="NOA"
    self.mess_history=[]  # history of alerts given with notifications on the ha screen so we don't duplicate them.  Cleared when no alerts are present.

    if "location" in self.args:
      self.loc=eval(self.args["location"])
    else:
      self.loc={}

    if "dash_dir" in self.args:
      self.dashdir=self.args["dash_dir"]
      self.dash_fileout=self.dashdir + "weatherAlert.html"
    else:
      self.dashdir=False
      self.dash_fileout=""

    if "title" in self.args:
      self.title=self.args["title"]
    else:
      self.title="Weather Alert"

    if "tz" in self.args:
      self.tz=eval(self.args["tz"])
    else:
      self.log("tz element must be configured")

    if "zmw" in self.loc:
      self.location=self.loc["zmw"]
    elif "zip" in self.loc:
      self.location=self.loc("zip")
    elif ("country" in self.loc) and ("city" in self.loc):
      self.location=self.loc["country"]+"/"+self.loc["city"]
    elif ("city" in self.loc) and ("state" in self.loc):
      self.location=self.loc["state"]+"/"+self.loc["city"]
    else:
      self.ha_config=self.get_plugin_config()
      self.log("ha_config={}".format(self.ha_config))
      self.location=str(self.ha_config["latitude"])+","+str(self.ha_config["longitude"])

    self.log("location={}".format(self.location))
    if "frequency" in self.args:
      self.freq=int(float(self.args["frequency"]))
    else:
      self.freq=15
    self.desired_alerts=self.args["alerts"]

    self.log("self.Location={}".format(self.location))
    self.log("Alert Levels={}".format(self.desired_alerts))
    self.log("Setting WeatherAlert to run ever {} minutes or {} seconds".format(self.freq,self.freq*60),"INFO")
    # you might want to use run_minutely for testing and run every (self.freq)  minutes for production.
    #self.run_minutely(self.getAlerts,start=None)
    self.run_every(self.getAlerts,self.datetime(),self.freq*60)
    self.run_every(self.getWeather,self.datetime(),self.freq*30)
    self.log("Initialization complete")

  def get_zone_by_lon_lat(self,**kwargs):
    url = "https://api.weather.gov/zones?type=forecast&point={}".format(self.location)
    myResponse = requests.get(url)
    self.log("myResponse.status_code={}".format(myResponse.status_code))

    # For successful API call, response code will be 200 (OK)
    if( not myResponse.ok):
      self.log("myResponse.status_code={}".format(myResponse.status_code))
      myResponse.raise_for_status()
    else:
      jData = json.loads(myResponse.content.decode('utf-8'))
    self.zone=jData["features"][0]["properties"]["id"]
    self.log("Returning zone = {}".format(self.zone))
    return(self.zone)

  def getWeather(self,kwargs):
    self.log("Checking Weather")
    rain_states=["rainy","snowy","snowy-rainy","hail","lightning"]
    if self.get_state("weather.dark_sky") in rain_states:
      self.set_state("sensor.raining",state="on")
    else:
      self.set_state("sensor.raining",state="off")

  ###########################
  def getAlerts(self,kwargs):
    self.log("checking for alerts")
    # Get Alert Data
    zone=self.get_zone_by_lon_lat()
    alert={}
    url="https://api.weather.gov/alerts/active/zone/{}".format(zone)

    myResponse = requests.get(url)
    self.log("myResponse.status_code={}".format(myResponse.status_code))

# For successful API call, response code will be 200 (OK)
    if( not myResponse.ok):
      self.log("myResponse.status_code={}".format(myResponse.status_code))
      myResponse.raise_for_status()
    else:
      # Loading the response data into a dict variable
      # json.loads takes in only binary or string variables so using content to fetch binary content
      # Loads (Load String) takes a Json file and converts into python data structure (dict or list, depending on JSON)
      jData = json.loads(myResponse.content.decode('utf-8'))

      self.log("The response contains {0} properties".format(len(jData["features"])))
      if len(jData["features"])==0:                                                              # if there aren't any alerts clean out the alertlog and skip the rest.
        self.log("No alerts at this time")
        self.mess_history=[]
      else:
        for a in jData["features"]:
          alert[a["properties"]["id"]]={"messageType":a["properties"]["messageType"],
                  "event":a["properties"]["event"],
                  "expires":a["properties"]["expires"],
                  "headline":a["properties"]["headline"],
                  "displayed":"N"}
        mess=""
        for a in alert:
          mess=mess+alert[a]["headline"] 
        self.log("mess={}".format(mess))
        self.sendAlert(alert)

  def bogus_stuff(self,**kwargs):
        for alert in jData["features"]:                                                  # Loop through all the alerts
          alert["id"]=alert["event"]+alert["expires"]                                  # setup a unique reproducable key for each alert 
          self.log("alert[type]={}".format(alert["type"]))
          if alert["type"] in self.desired_alerts:                                     # is this an alert type we are interested in
            if not alert["key"] in self.alertlog:                                      # if the key is in the alertlog we have already alerted on it
              if self.timefromstring(alert["expires"])<datetime.datetime.now():        # has this alert expired?
                self.log("Alert has expired {}".format(alert),"INFO")
              else:                                                                    # nope it has not expired
                self.alertlog[alert["key"]]=alert["expires"]                           # put the key and expire date into the alertlog so we don't show it again
                self.log("this is an alert we are interested in {}".format(alert["type"]),"INFO")
                if "message" in alert:                                                 # Alert using a persistent notification ( you could add other methods of alerting here too)
                  self.sendAlert(alert["message"])
                  if not self.dashdir==False:
                    if not fileopen==False:
                      fout=open(self.dash_fileout,"w")
                      fout.write("<html><head><style>body { background-color: #ff0000; } </style></head><body>")
                      fileopen=True
                    fout.write(alert["message"])
                    fout.write("<P>")
                else:
                  self.sendAlert(alert["level_meteoalarm_description"])
                  if not self.dashdir==False:
                    if not fileopen==False:
                      fout=open(self.dash_fileout,"w")
                      fout.write("<html><head><style>body { background-color: #ff0000; } </style></head><body>")
                      fileopen=True
                    fout.write(alert["level_meteoalarm_description"])
                    fout.write("<P>")
            else:                                                                      # we have already notified on this so don't do it again
              self.log("Alert already in list")
          else:                                                                        # there is an alert but we aren't interested in this type
            self.log("we are not interested in alert type {}".format(alert["type"]),"INFO")
        if fileopen==True:
          fout.write("</body></html>")
          fout.close()
        else:
          self.clean_dashfile(self.dashdir,self.dash_fileout)

  def clean_dashfile(self,dashdir,fname):
    if dashdir:
      if os.path.isfile(self.dash_fileout):
        self.log("removing {}".format(self.dash_fileout))
        os.remove(self.dash_fileout)
  

  #######################
  #
  # send the proximity alert and send it to speak if it's installed
  #
  #######################
  def sendAlert(self,alert):
    title=alert[list(alert)[0]]["event"]
    message=alert[list(alert)[0]]["headline"]
    if not message in self.mess_history:
      self.mess_history.append(message)
      self.call_service("persistent_notification/create",title=title,message=message)   # send persistent_notification 
    if not  self.get_app("speak")==None:                                                    # check if speak is running in AppDaemon
      self.log("Speak is installed")
      priority=1
      self.fire_event("SPEAK_EVENT",text=message,media_player="all",priority=priority,language="en")               # Speak is installed so call it
    elif not self.get_app("soundfunctions")==None:
      self.log("Soundfunctions is installed")
      sound = self.get_app("soundfunctions")                                                 
      sound.say("Any text you like","your_language","your_priority")    
    else:
      self.log("No supported speack apps are installed")                                                    # Speak is not installed


  #######################
  # Had some problems getting weather undergrounds date format to behave so I had to parse it out myself
  #######################
  def timefromstring(self,instr):
    # This is weather undergrounds timestamp format.  Notice the "on" in the middle.  This caused a problem.
    # h:mm AM TZZ on month dd, yyyy

    strtime=instr[0:instr.find("on")-1]
    if len(strtime[:strtime.find(":")])==1:
      strtime="0"+strtime[:len(strtime)-3]

    strdate=instr[instr.find("on")+3:]
    combineTime=strdate+" " + strtime.strip()
    dtformat="%B %d, %Y %I:%M %p"
    for tzi in self.tz:
      if combineTime.find(tzi)>=0:
        dtformat=dtformat+" %Z"
        break

    self.log("combineTime={}, {}".format(combineTime,dtformat))
    tdate=datetime.datetime.strptime(combineTime,dtformat)
    return tdate

