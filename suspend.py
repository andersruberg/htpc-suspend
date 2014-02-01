#!/usr/bin/python
#############################################################
# HTPC suspend script                                       #
# author: Anders Ruberg                                     #            
# based on http://ubuntuforums.org/showthread.php?t=1423030 #
# by Hans van Schoot                                        #
#############################################################
# TODO list: build in a check for ftp server activity
# turn the script into nice program with modules

# The purpose of this script is to suspend the machine if it's idle.
# the script checks:
# - if a lockfile is present (this way the script can be bypassed when needed)
# - if XBMC is running, and if it's playing
# - if there is keyboard or mouse activity
# - if transmission download speed is too low to keep the system awake for
# - if there are samba shares in use (READ ON FOR THIS!)

# To function properly this script needs a couple things:
# - from apt-get: xprintidle
# - from apt-get: transmissioncli
# - the gnome-power-control script (installed in /usr/bin) from AgenT: http://ubuntuforums.org/showpost.php?p=8309702&postcount=16
# - xbmc web server enabled without a password (can be found in xmbc settings under network) 
#     (if you don't need xbmc, you can comment out the xbmc section or put the xbmcDelay on 0)
# - to be able to use "sudo smbstatus" (so rootaccess, or if you run the script on userlevel this can be fixed by adding
#     "your_username ALL=(ALL) NOPASSWD: /usr/bin/smbstatus" visudo (run "sudo visudo" in terminal))
# the same goes for sudo /usr/sbin/pm-suspend !!!!! the suspend command!


#############################
# Settings and delay values #
#############################
# the system suspends only if all the different items are idle for a longer time than specified for it
# the values are in minutes, unless you change the sleep command at the start of the loop
xbmcDelay = 30
sambafileDelay = 30
xDelay = 0 #currently broken, XBMC Dharma beta 2 generates X events...
transmissionDelay = 10
# these deltas are the minimum time between 2 backups, or the running of flexget
# flexget automaticly runs on wakeup of the machine
# do not remove datetime import line!
from datetime import *
backupDelta = timedelta(hours=24)
flexgetDelta = timedelta(hours=2)

# this is the path to the lockfile you can use.
# to lock the system, just use the touchcommand: "touch /home/media/.suspendlockfile" (or create a starter to it)
# to unlock the system, just use rmcommand "rm /home/media/.suspendlockfile" (or create a starter to it)
lockfilelist = [
'/home/anders/.suspendlock'
]
# the path to the xmbc webserver, edit this if you use another port for instance
#xbmcAdressJSON = "http://127.0.0.1:8080/jsonrpc"

url = "http://127.0.0.1:8080/jsonrpc"

# command to contact the transmission server, -n is user/pass
transmissionAdress = "transmission-remote -n anders:spagetti "
# minimal download speed required to keep the system awake
transmissionSpeed = 10.0


##### SAMBACHECK SETTINGS #######
# the script checks the output of sudo smbstatus to see if there are locked files 
# (usualy someone downloading or playing media from the system)
# if no locked files are found, it checks if there are folders in use that should keep the system awake
# 
# smbimportantlist is a list of strings the sambashare should check if they are in use (for instance a documents folder)
# to find out what to put here: 
# 1. connect to the share with another computer
# 2. use "sudo smbstatus" in console
# 3. check for the name of the share, it's printed out under "Service"
#
# makeup of the list is: [ 'item1' , 'item2' , 'item3' ]
smbimportantlist = [
#'movies',
#'anders',
#'pictures',
#'music',
#'video',
#'torrentflux'
]


# change this to False if you want the script to run silent
debugmode = False
LOG_DEBUG = "debug"
LOG_INFO = "info"
import syslog

def log(string, type=LOG_INFO):
    if (type == LOG_DEBUG) and debugmode:
        print string
    else:
        #print "Suspend Manager says: " + string
        syslog.syslog("Suspend Manager says: " + string)
        if debugmode:
            print string


### the script starts here
from os import *
from urllib2 import *
from time import sleep
import requests
import json
import httplib
import sys
import subprocess


xbmcIdletime = 0
sambaIdletime = 0
transmissionIdletime = 0
Lockfile = 0
keeponrunnin = True
startup = True
newfiles = False
backupDate = datetime.now()
flexgetDate = datetime.now()
sshActive = False

# this is the loop that keeps the script running. the sleep command makes it wait one minute
# if you want to increase/decrease the frequencies of the checks, change the sleeptimer.
# keep in mind that this wil change the Delay times for xbmc and samba
while keeponrunnin:
    #print "\n !!! Niet dichtdoen!!!\n Dit schermpje moet de pc in slaapstand zetten!\n"

# aditional lines to make flexget run directly after a suspend, even if the last flexget was less than 2 hours ago
#    if startup:
#        sleep(10)
#        print popen('flexget').read()
#        flexgetDate = datetime.now()
#        startup = False



# this part checks if transmission and xbmc are idle. if there are new files (newfiles gets activated when transmission is downloading, so if transmission is idle again the torrents should be finished. another trick would be to check the transmission-remote output for torrents that are completed and move them)
#    if transmissionIdletime >= 3 and xbmcIdletime >= 3 and newfiles:
#        print popen('/home/media/showmover.py').read() #this is a script i'm using to move downloaded files into the right TV show directory
#        print "updating the xbmc video Library"
#        try: handle = urlopen(xbmcAdressJSON, '{"jsonrpc": "2.0", "method": "VideoLibrary.ScanForContent", "id": "1"}')
#        except IOError, e:
#            print "jsonrpc is not responding..."
#        else:
#            newfiles = False


# this checks when the mouse and keyboard were touched, and converts the time to minutes
#   try: xIdletime = int(popen('xprintidle').read())/60000
#   except IOError, e:
#       if debugmode:
#           print "xprintidle is not installed? use sudo apt-get install xprintidle"
        

  # Check if any ssh connections are open to the server
    #connections = subprocess.Popen(['lsof','-i','-n','-P'], shell=False, stdout=subprocess.PIPE).communicate()[0].split('\n')
    #netstat = subprocess.Popen(['netstat', '-n', '--protocol', 'inet'], shell=False, stdout=subprocess.PIPE)
    #connections = subprocess.check_output(('grep', '\':22\''), stdin=netstat.stdout)
    ps = subprocess.Popen('netstat -n --protocol inet | grep \':22\'', shell=True, stdout=subprocess.PIPE)
    #.communicate()[0].split('\n')
    #'netstat', '-n', '--protocol inet', '| grep \':22\''
    i=0
    for line in ps.stdout:
        i+=1
    if i:
        sshActive = True
    else:
        sshActive = False
    
    active_players = {"jsonrpc": "2.0", "method": "Player.GetActivePlayers", "id": 1}
    screensaver_active = {"jsonrpc": "2.0", "method": "XBMC.GetInfoBooleans", "params": { "booleans": ["System.ScreenSaverActive "] }, "id": 1}
    headers = {'content-type': 'application/json'}

    r = requests.post(url, data=json.dumps(active_players), headers=headers)
    if r.status_code == 200:
        content = json.loads(r.content)
        if content.has_key("result"):
            if len(content["result"]):
                #print "XBMC is playing something"
                xbmcIdletime = 0
            else:
                #print "Nothing is playing in XBMC"
                xbmcIdletime += 1
    else:
        log("XBMC webinterface (jsonRPC) is not responding, checking if xbmc is running")
        psgrepxbmc = popen("ps -e | grep xbmc").read()
        if len(psgrepxbmc) == 0:
            log("XBMC not found using grep, most likely not running! starting XBMC...")
            system("xbmc &")
        else:
            log("XBMC is running, but jsonrpc is not responding")
            xbmcIdletime += 1


# counting the number of lockfiles
    Lockfile = 0
    for i in lockfilelist:
        if path.exists(i):
            Lockfile += 1

#######################################
# next section is the samba checkpart #
#######################################
    try: sambainfo = popen('sudo smbstatus').read()
    except IOError, e:
        log("No Sambaserver found, or no sudorights for smbstatus", LOG_DEBUG)
        sambaIdletime += 1 
    else:
        # first we check for file-locks
        if sambainfo.find('Locked files:\n') >= 0:
            sambaIdletime = 0
            log("a locked samba file has been found", LOG_DEBUG)
        # if no locked files, strip the info and look for keywords, if found reset idletime
        else:
            sambaIdletime += 1
            sambasplit = sambainfo.split('\n')[4:-4]
            sambasplit.reverse()
            for i in sambasplit:
                if i == '-------------------------------------------------------':
                    break
                for j in smbimportantlist:
                    # check to filter out crashes on empty lines
                    if len(i.split()) >= 1:
                        if i.split()[0].find(j) >= 0:
                            sambaIdletime = 0
                            log("an important samba share is in use", LOG_DEBUG)


# this is the check for torrent activity. it checks the last value in the last line
# from the transmission-remote command, which is the downloadspeed in kb/s
    try: transmissioninfo = popen(transmissionAdress + "-l").read()
    except IOError, e:
        log("transmissioncli not installed", LOG_DEBUG)
        transmissionIdletime += 1
    else: 
        if transmissioninfo == '':
            transmissionIdletime += 1
            log("transmission not active", LOG_INFO)
        elif float(transmissioninfo.split()[-1]) >= transmissionSpeed:
                transmissionIdletime = 0
                newfiles = True
                log("transmission is downloading @ %s kb/s" %(transmissioninfo.split()[-1]), LOG_DEBUG)
        else:
            transmissionIdletime += 1



# a check to see if we can run backup scripts
#    if xbmcIdletime >=3 and xIdletime >=3 and sambaIdletime >=3 and Lockfile == 0:
#        currenttime = datetime.now()
#        if (currenttime - backupDate) >= backupDelta:
#            # backup the files using linkcopy, combined with Rsyncing to the original backup location gives recursives backups
#            print "backing up the system now..."
#            system('cp -al /media/drive2/Backups /media/drive2/Backups-old/backup-%i-%i-%i'%(currenttime.year,currenttime.month,currenttime.day))
#            backupDate = datetime.now()
#            print "rsyncing the current Backupfolder to the other harddisk, this should be fast if not too much has changed"
#            system('rsync -a /media/drive2/Backups /media/drive1/Backup-mirror')


# this part runs flexget if xbmc is idle and the flexget hasn't been run in the last 2 hours 
#    if xbmcIdletime >=3:
#        currenttime = datetime.now()
#        if (currenttime - flexgetDate) >= flexgetDelta:
#            print popen('flexget').read()
#            flexgetDate = datetime.now()



# this is the final check to see if the system can suspend. 
# uncomment the print statements and run in terminal if you want to debug/test the script
    if xbmcIdletime >= xbmcDelay and transmissionIdletime >= transmissionIdletime and sambaIdletime >= sambafileDelay and Lockfile == 0 and sshActive == False:
        log("Suspending system NOW!")
        system('sudo /usr/sbin/pm-suspend')
        xbmcIdletime = 0
        startup = True
        sambaIdletime = 0
        transmissionIdletime = 0
    else:
        status = "System is active! XBMC is idle for " + str(xbmcIdletime) + " minutes."
        status += " Samba is idle for " + str(sambaIdletime) + " minutes."
        status += " Transmission is idle for " + str(transmissionIdletime) + " minutes."
        if Lockfile == 0:
            status += " No lock file present."
        else:
            status = status + " There are lock files found."

        if sshActive == False:
            status = status + " No active SSH connection(s)."
        else:
           status = status + " There are active SSH connection(s) found."
        log(status)

    sleep(60) # this is the delay that runs the script every minute, lower this value for testing!
