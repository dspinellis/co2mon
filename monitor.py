#!/usr/bin/env python

# based on code by henryk ploetz
# https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us

import datetime,sys, fcntl, os, argparse
from time import time, sleep

# Netdata update interval. This is the time actually taken to refresh an
# entire record
update_every = 20

def decrypt(key,  data):
    cstate = [0x48,  0x74,  0x65,  0x6D,  0x70,  0x39,  0x39,  0x65]
    shuffle = [2, 4, 0, 7, 1, 6, 5, 3]

    phase1 = [0] * 8
    for i, o in enumerate(shuffle):
        phase1[o] = data[i]

    phase2 = [0] * 8
    for i in range(8):
        phase2[i] = phase1[i] ^ key[i]

    phase3 = [0] * 8
    for i in range(8):
        phase3[i] = ( (phase2[i] >> 3) | (phase2[ (i-1+8)%8 ] << 5) ) & 0xff

    ctmp = [0] * 8
    for i in range(8):
        ctmp[i] = ( (cstate[i] >> 4) | (cstate[i]<<4) ) & 0xff

    out = [0] * 8
    for i in range(8):
        out[i] = (0x100 + phase3[i] - ctmp[i]) & 0xff

    return out

def hd(d):
    return " ".join("%02X" % e for e in d)

def now():
    return int(time.time())

def monitor(port, out, nvalues, csv_output, header_output, netdata_output,
            interval):
    """Monitoring loop"""
    global update_every

    key = [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]
    fp = open(port, "a+b",  0)
    HIDIOCSFEATURE_9 = 0xC0094806
    set_report = "\x00" + "".join(chr(e) for e in key)
    fcntl.ioctl(fp, HIDIOCSFEATURE_9, set_report)

    values = {}
    last_run = dt_since_last_run = 0
    while True:
        byte_data = fp.read(8)
        data = list(byte_data)

        if data[4] == 0x0d and (sum(data[:3]) & 0xff) == data[3]:
            decrypted = data
        else:
            decrypted = decrypt(key, data)

        if decrypted[4] != 0x0d or (sum(decrypted[:3]) & 0xff) != decrypted[3]:
            print(hd(data), " => ", hd(decrypted),  "Checksum error",
                  file=sys.stderr)
            continue
        op = decrypted[0]
        val = decrypted[1] << 8 | decrypted[2]
        values[op] = val

        if (0x50 not in values) or (0x42 not in values):
            continue

        co2 = values[0x50]
        temperature = (values[0x42]/16.0-273.15)

        if netdata_output:
            # Gather telegrams until update_every has lapsed
            # https://github.com/firehol/netdata/wiki/External-Plugins
            now = time()
            if last_run > 0:
                dt_since_last_run = now - last_run
            if last_run != 0 and dt_since_last_run < update_every:
                continue
            # Express dt in integer microseconds
            dt = int(dt_since_last_run * 1e6)

            print(f"BEGIN Air.temperature {dt}")
            print(f"SET t = {temperature:.1f}")
            print('END')

            print(f"BEGIN Air.co2 {dt}")
            print(f"SET co2 = {co2}")
            print('END')

            last_run = now

        if csv_output:
            if header_output:
                out.write("timestamp,temperature,CO2\n")
                header_output = False
            ts = (datetime.datetime
                  .now()
                  .astimezone()
                  .replace(microsecond=0)
                  .isoformat())
            out.write(f"{ts},{temperature:.1f},{co2}\n")
        elif not netdata_output:
            out.write(f"CO₂: {co2:4d} ppm; Temp: {temperature:3.1f} °C    \r")
            out.flush()
        if interval:
            sleep(interval)

        if nvalues:
            nvalues -= 1
            if nvalues == 0:
                return


def netdata_configure():
    """Configure the supported Netdata charts
    See https://learn.netdata.cloud/docs/contributing/external-plugins/
    CHART type.id name title units [family [context [charttype [priority [update_every [options [plugin [module]]]]]]]]
    DIMENSION id [name [algorithm [multiplier [divisor [options]]]]]
    """
    sys.stdout.write("""
CHART Air.temperature 'T' 'Temperature' 'Celsius'
DIMENSION t 'Air temperature'

CHART Air.co2 'CO2' 'CO2 concentration' 'ppm'
DIMENSION co2 'CO2 concentration'
""")

def main():
    """Program entry point"""

    global update_every

    # Remove any Netdata-supplied update_every argument
    if 'NETDATA_UPDATE_EVERY' in os.environ:
        update_every = int(sys.argv[1])
        del sys.argv[1]

    parser = argparse.ArgumentParser(
        description='CO2 monitoring program')
    parser.add_argument('-c', '--csv',
                        help='Output CSV records',
                        action='store_true')
    parser.add_argument('-H', '--header',
                        help='Print CSV header',
                        action='store_true')
    parser.add_argument('-i', '--interval', type=float,
                        help='Interval between output values')
    parser.add_argument('-N', '--netdata',
                        help='Act as a netdata external plugin',
                        action='store_true')
    parser.add_argument('-n', '--nvalues', type=int,
                        help='Number of values to process (default: infinite)')
    parser.add_argument('-o', '--output',
                        help='Specify CSV output file (default: stdout)')
    parser.add_argument('-p', '--port',
                        help='Serial port to access (default: /dev/hidraw0)',
                        default='/dev/hidraw0')

    args = parser.parse_args()
    if args.output:
        out = open(args.output, 'a')
    else:
        out = sys.stdout
    if args.netdata:
        netdata_configure()
    monitor(args.port, out, args.nvalues, args.csv, args.header, args.netdata, args.interval)

if __name__ == "__main__":
    main()
