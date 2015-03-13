#!/bin/python

import os
import re
import sys
import subprocess
import sqlite3
import signal
from time import sleep

new_env = os.environ.copy()
new_env['DISPLAY'] = ':0'

def get_active_window():
	info = {}
	
	root = subprocess.Popen(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stdout=subprocess.PIPE, env=new_env)

	id_w = None
	id_p = None
	for line in root.stdout:
		m = re.search('^_NET_ACTIVE_WINDOW.* ([\w]+)$', line)
		if m != None:
			id_ = m.group(1)
			info['id'] = id_
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

sleeptime = 1
savetime = 300

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
	for row in commonapps:
		print ' '.join(map(str, row))
	for row in commonwindows:
		print ' '.join(map(str, row))

if "-q" in sys.argv:
	query()
	raise SystemExit()

dat = {}
i = savetime
while True:
	info = get_active_window()
	name = info.get('exe', 'unknown')
	title = info.get('name', 'unknown')
	
	name = os.path.split(name)[-1]

	with con:
		cur.execute("INSERT OR IGNORE INTO wc(Name, Title) VALUES (?, ?)", (name,title))
		cur.execute("UPDATE wc SET Count=Count+? WHERE Name = ? AND Title = ? AND Date = date('now')", (sleeptime,name,title))
	
	i += sleeptime
	if i > savetime:
		print "Saving"
		con.commit()
		i -= savetime
	
	sleep(sleeptime)
		

