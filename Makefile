
install:
	cp windowcounter.service /etc/systemd/system/windowcounter.service
	systemctl enable windowcounter

uninstall:
	systemctl disable windowcounter
	rm -f /etc/systemd/system/windowcounter.service

