# weatherAlert
Weather Alert application for AppDaemon and HomeAssistant

Make sure your home knows about any severe weather approaching.  WeatherAlert sends a persistent_notification to your HA desktop with with information on any severe weather alerts in your area.

Weather alerts is configurable to only show you the alerts you are interested in seeing.  

Installation Instructions
<ul>
<li>Clone this repository in your AD code directory.  It should create a weatherAlert directory.    
<li>Add the following lines to your appDaemon config file<P>
     [weatherAlert]<br>
     module=weatherAlert<br>
     class=weatheralert<br>
     alerts = {"HEA","TOR"}<br>
     key = your weather underground key<br>
   * location={"city":"your city","state":"your state"}  or {"zmw":"your zmw"}`<br>
   * frequency=minutes between checks   ( Defaults to 15 min )<br>
   * title=title of persistent notification window<br>
</ul>
Notes
<ul>
<li>* represent optional entries (do not include *)
<li>location can be expressed as a dictionary containing the following:
<ul><li>{"city":"your city", "state":"your state"}
<li>{"zip":"your zip code"}
<li>{"Country":"Your country name","city":"Your city"}
<li>if location is not in the config file, it defaults to your HomeAssistant Latitude/Longitude
</ul>
<li>Possible values for alerts are : type	Translated<br>
                                    <t>HUR	Hurricane Local Statement<br>
                                    <t>TOR	Tornado Warning<br>
                                    <t>TOW	Tornado Watch<br>
                                    <t>WRN	Severe Thunderstorm Warning<br>
                                    <t>SEW	Severe Thunderstorm Watch<br>
                                    <t>WIN	Winter Weather Advisory<br>
                                    <t>FLO	Flood Warning<br>
                                    <t>WAT	Flood Watch / Statement<br>
                                    <t>WND	High Wind Advisory<br>
                                    <t>SVR	Severe Weather Statement<br>
                                    <t>HEA	Heat Advisory<br>
                                    <t>FOG	Dense Fog Advisory<br>
                                    <t>SPE	Special Weather Statement<br>
                                    <t>FIR	Fire Weather Advisory<br>
                                    <t>VOL	Volcanic Activity Statement<br>
                                    <t>HWW	Hurricane Wind Warning<br>
                                    <t>REC	Record Set<br>
                                    <t>REP	Public Reports<br>
                                    <t>PUB	Public Information Statement<br>

  <li>If you are using the following speach apps in appdaemon
  <ul><li>sound - by Rene Tode - https://community.home-assistant.io/t/let-appdaemon-speak-without-tts-and-mediaplayer-in-hass/8058
  <li>speak - by Chip Cox - https://github.com/turboc1208/AppDaemonApps/blob/master/speak.py
   weatherAlert will recognize them and send alerts to your speakers as well#  as the persistent_notifications.
</ul>
</ul>

 Visit the weatherunderground at the following link for more information about this API
 https://www.wunderground.com/weather/api/d/docs?d=data/alerts
