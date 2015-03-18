#!/bin/python

import os
import re
import sys
import subprocess
import sqlite3
import signal
import datetime
import time
from time import sleep

#TODO: http://askubuntu.com/questions/202136/how-can-a-script-detect-a-users-idle-time
#http://stackoverflow.com/questions/1770209/run-child-processes-as-different-user-from-a-long-running-process/6037494#6037494

new_env = os.environ.copy()
new_env['DISPLAY'] = ':0'

def get_active_window():
	info = {}
	
	root = subprocess.Popen(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stdout=subprocess.PIPE, env=new_env)

	id_w = None
	id_p = None
	for line in root.stdout:
		#m = re.search('^_NET_ACTIVE_WINDOW.* ([\w]+)$', line)
		m = re.search('^_NET_ACTIVE_WINDOW.* (0x[0-9A-F]+)$', line)
		if m != None:
			id_ = m.group(1)
			info['id'] = int(id_, 0)
			if info['id'] > 0:
				id_w = subprocess.Popen(['xprop', '-id', id_, 'WM_NAME'], stdout=subprocess.PIPE, env=new_env)
				id_p = subprocess.Popen(['xprop', '-id', id_, '_NET_WM_PID'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=new_env)
			break

	if id_w != None:
		for line in id_w.stdout:
			match = re.match("WM_NAME\(\w+\) = (?P<name>.+)$", line)
			if match != None:
				info['name'] = match.group("name")

	if id_p != None:
		(out, err) = id_p.communicate()
		if id_p.returncode == 0:
			try:
				pid = int(out.split()[-1])
				info['pid'] = pid
			except ValueError:
				pass
			
			if pid != -1:
				exe = os.path.realpath('/proc/' + str(pid) + '/exe')
				info['exe'] = exe
			
	return info

sleeptime = 5
savetime = 300
warnsame = 60*5
dontwarn = ['gedit']

thisdir = os.path.dirname(os.path.realpath(__file__))
home = os.path.expanduser("~")

#con = sqlite3.connect(os.path.join(thisdir, 'windowcounter.db'))
con = sqlite3.connect(os.path.join(home, '.windowcounter.db'))
con.text_factory = str

def signal_handler(signal, frame):
	print('Saving')
	con.commit()
	raise SystemExit()

signal.signal(signal.SIGINT, signal_handler)

with con:
	cur = con.cursor()	
	cur.execute('SELECT SQLITE_VERSION()')
	cur.execute("CREATE TABLE IF NOT EXISTS wc (Id INTEGER PRIMARY KEY, Name TEXT, Title TEXT, Date DATE DEFAULT CURRENT_DATE, Count INTEGER DEFAULT 1, CONSTRAINT UQ_Name_Date UNIQUE(Name, Title, Date))")

def query():
	with con:
		cur.execute("SELECT sum(Count), Name FROM wc WHERE Date = date('now') AND Name != 'unknown' GROUP BY Name ORDER BY sum(Count) DESC")
		commonapps = cur.fetchall()
		cur.execute("SELECT Count, Name, Title FROM wc WHERE Date = date('now') AND Name != 'unknown' ORDER BY Count DESC LIMIT 10")
		commonwindows = cur.fetchall()
	print "By Process"
	for row in commonapps:
		time = datetime.timedelta(seconds=row[0])
		print "", time, ' '.join(map(str, row[1:]))
	print "Top Titles"
	for row in commonwindows:
		time = datetime.timedelta(seconds=row[0])
		print "", time, ' '.join(map(str, row[1:]))

if "-q" in sys.argv:
	query()
	raise SystemExit()

dat = {}
i = savetime
start_time = time.time()
last_time = start_time
timecheck = 0
windowtime = 0
lastwindow=""
while True:
	this_time = time.time()
	while this_time - last_time > sleeptime:
		elapsed_time = this_time - last_time
		last_time += sleeptime

		info = get_active_window()
		name = info.get('exe', 'unknown')
		title = info.get('name', 'unknown')
	
		name = os.path.split(name)[-1]

		with con:
			cur.execute("INSERT OR IGNORE INTO wc(Name, Title) VALUES (?, ?)", (name,title))
			cur.execute("UPDATE wc SET Count=Count+? WHERE Name = ? AND Title = ? AND Date = date('now')", (sleeptime,name,title))
			timecheck += sleeptime
	
		if lastwindow == name:
			windowtime += sleeptime
			if windowtime >= warnsame:
				if name not in dontwarn:
					#os.system("locate -r '\.wav$' | head -n $(( ( RANDOM % 200 )  + 1 )) | tail -4 | xargs -I {} paplay \"{}\"")
					subprocess.Popen(['paplay', '/usr/share/sounds/pop.wav'], stdout=subprocess.PIPE, env=new_env)
					subprocess.Popen(['notify-send', '-t', '5000', 'GET BACK TO WORK!!!'], stdout=subprocess.PIPE, env=new_env)
				windowtime = 0
		else:
			windowtime = 0
		lastwindow = name
	
		#query()
	
		i += elapsed_time
		if i > savetime:
			#print "Saving"
			#sys.stderr.write(str(this_time - start_time) + " " + str(timecheck) + "\n")
			con.commit()
			i -= savetime
	
	sleep(1)
		

