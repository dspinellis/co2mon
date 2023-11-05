# CO2mon

The _co2mon_ program is a [netdata](https://www.netdata.cloud/) plugin
and a simple command-line tool for measuring and reporting CO₂
and temperature values.
It is based on the [officeweather](https://github.com/wreiner/officeweather)
software developed by [Walter Reiner](http://www.wreiner.at/).

The _co2mon_ software reads data from TFA-Dostmann sensors. It can then
* act as a [netdata](https://www.netdata.cloud/) plugin,
* output real-time values,
* output and store CSV values.

## Hardware requirements

Multiple CO2 Sensors are supported:

    - [TFA-Dostmann AirControl Mini CO2 Messgerät](http://www.amazon.de/dp/B00TH3OW4Q) -- 65 euro (sends encrypted data)
    - [TFA-Dostmann AIRCO2NTROL Coach CO2 Monitor](http://www.amazon.de/dp/B07R4XM9Z6) -- 72 euro (sends unencrypted data)


## Installation
Run `sudo make install`.
This will install the `co2mon` command-line program in the `/usr/local/bin`
directory.

### Real-time command-line output
Assuming the monitoring hardware appears in the default `/dev/hidraw0`,
run `sudo co2mon` to see the CO₂ values in real time.
Run `co2mon --help` to see how you can adjust the program's operation.

### Use as a Netdata plugin
Copy the `co2mon.py` file to the location when the Netdata plugins are
stored, with a suffix ending in `.plugin`,
e.g. `cp co2mon.py /usr/lib/netdata/plugins.d/co2mon.plugin`.
Also, configure the USB port with a _udev_ rule, such as the following
```
SUBSYSTEMS=="usb", ACTION=="add", ATTRS{product}=="USB-zyTemp", MODE="0664", GROUP="netdata", SYMLINK+="co2monitor"
```

If you also intend to collect data in a CSV file,
create the file setting its owner and group to `netdata`.

### Run in the background to record data to a file
You can arrange for the _co2mon_ program to be run at boot time through a
_cron_(8) `@reboot` rule, by adding the command to the `rc.local` file,
or by configuring, enabling, and starting a _systemd_(1) service.
For the _systemd_ alternative, create a _systemd_ service file
(e.g. in `/etc/systemd/system/co2mon.service`) with contents such as the
those of the [co2mon.service](co2mon.service) file provided in this
repository.

## License

[MIT](http://opensource.org/licenses/MIT)
