import csv
import ipaddress
import sys
import os
from urllib.request import Request, urlopen
import io

netbox = 'https://netbox.minserver.dk/ipam/prefixes/?status=1&parent=&family=&q=&vrf=npflan&mask_length=&export'
req = Request(netbox, headers={'User-Agent': 'Mozilla/5.0'})
data = urlopen(req).read()

datafile = os.path.join(os.path.dirname(__file__), 'data.csv')
with open(datafile, 'wb+') as f:
    f.write(data)

reader = csv.DictReader(io.StringIO(data.decode()), delimiter=',', quotechar='|')

print('default-lease-time 7200;')
print('max-lease-time 28800;\n')
print('authoritative;\n')
print('option domain-name "npf";\n')
print('option domain-name-servers 10.96.5.1;\n')

print('omapi-port 7911;')
print('omapi-key omapi_key;\n')

print('key omapi_key {')
print('\t algorithm hmac-md5;')
print('\t secret LsMkrX1xprEQQBoeGAC6NvokcA/mcuD5LnBqD/2gxJEpZqTTRN7vtPm0BVW03zl0oo1qWCVrNTqsoAq2B8hrsg==;')
print('};\n')

# Argument to generate include for high availability config
if len(sys.argv) > 1 and sys.argv[1] == "master":
    print('include "/etc/dhcpd.master";\n')
elif len(sys.argv) > 1 and sys.argv[1] == "slave":
    print('include "/etc/dhcpd.slave";\n')
else:
    print('include "/dhcp/failover/dhcpd.failover";\n')

print('subnet 10.90.0.0 netmask 255.255.0.0 {}\n')

for row in reader:
    if row['role'].lower() == "Access".lower() or row['role'].lower() == "Wireless".lower() or row['description'].lower() == "AP-MGMT".lower():
        if row['description'].lower() == 'Wireless Networks'.lower():
            continue;
        print("# " + ' - '.join((n for n in (row['role'], row['description']) if n)))
        ip = ipaddress.IPv4Network(row['prefix'])
        parts = ip.with_netmask.split('/')
        network = parts[0]
        subnetmask = parts[1]
        print("subnet " + network + " netmask " + subnetmask + " {")
        print("\t pool {")
        print("\t\t range " + str(ip[4]) + " " + str(ip[pow(2, (32-ip.prefixlen))-6]) + ";")
        print('\t\t failover peer "failover-partner";')
        print("\t\t option routers " + str(ip[1]) + ";")
        print("\t}")
        print("}\n")
