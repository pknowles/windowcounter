
# Window Counter

A python script which polls for the current active window using `xprop` and records the executable name and window title.
With it you can see how much time you've spent procrastinating each day.

Comes with a fedora service file and Makefile to install with. An sqlite3 database is stored at `~/.windowcounter.db`.
To query the results, run `./windowcounter.py -q`.
