#############################################################
# HTPC suspend script                                       #
# author: Anders Ruberg                                     #            
# based on http://ubuntuforums.org/showthread.php?t=1423030 #
# by Hans van Schoot                                        #
#############################################################
TODO list: build in a check for ftp server activity
turn the script into nice program with modules

The purpose of this script is to suspend the machine if it's idle.
the script checks:
- if a lockfile is present (this way the script can be bypassed when needed)
- if XBMC is running, and if it's playing
- if there is keyboard or mouse activity
- if transmission download speed is too low to keep the system awake for
- if there are samba shares in use (READ ON FOR THIS!)

To function properly this script needs a couple things:
- from apt-get: xprintidle
- from apt-get: transmissioncli
- the gnome-power-control script (installed in /usr/bin) from AgenT: http://ubuntuforums.org/showpost.php?p=8309702&postcount=16
- xbmc web server enabled without a password (can be found in xmbc settings under network) 
    (if you don't need xbmc, you can comment out the xbmc section or put the xbmcDelay on 0)
- to be able to use "sudo smbstatus" (so rootaccess, or if you run the script on userlevel this can be fixed by adding
    "your_username ALL=(ALL) NOPASSWD: /usr/bin/smbstatus" visudo (run "sudo visudo" in terminal))
the same goes for sudo /usr/sbin/pm-suspend !!!!! the suspend command!
