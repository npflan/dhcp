import csv
import ipaddress
import sys
import os

datafile = os.path.join(os.path.dirname(__file__), 'data.csv')
with open(datafile, newline="") as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='|')

    print('default-lease-time 600;')
    print('max-lease-time 7200;\n')
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

    print('subnet 10.90.0.0 netmask 255.255.0.0 {')
    print('}\n')

    for row in reader:
        if row[7].lower() == "Access".lower() or row[7].lower() == "Wireless".lower():
            print("# " + row[7])
            ip = ipaddress.IPv4Network(row[0])
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
