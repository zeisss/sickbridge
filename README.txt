SickBridge
==========

Checks your SickBeard server for episodes to download and checks Serienjunkies.org for the downloadable files.
If found, it pushes them to JDownloader for downloading (You still have to enter the captchas!).

REQUIREMENTS
============
SickBridge
JDownloader
Python 2.7

INSTALL
=======
1. Grab the code and unpack somewhere
2. Enable WebInterface for JDownloader (We currently do not use the RemoteControl API)
3. Edit sickbridge.py if you have non-default ports for SickBeard or JDownloader
4. Start the script with either run.cmd (Windows) or the sickbridge.py directly