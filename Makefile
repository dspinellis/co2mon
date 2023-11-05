install:
	mkdir -p /usr/local/bin
	install  co2mon.py /usr/local/bin/co2mon
	test -d /usr/lib/netdata/plugins.d/ && install  co2mon.py /usr/lib/netdata/plugins.d/co2mon.plugin
