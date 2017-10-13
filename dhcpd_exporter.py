from isc_dhcp_leases import Lease, IscDhcpLeases
from prometheus_client.core import (
    GaugeMetricFamily, REGISTRY
)
import prometheus_client
import urllib
import os
import csv
import io
from ipaddress import IPv4Network, IPv4Address
from collections import defaultdict

import sys
import time

class DhcpdCollector(object):
    def __init__(self, leasefile='/var/lib/dhcp/dhcpd.leases'):
        print(leasefile)
        netbox = 'https://netbox.minserver.dk/ipam/prefixes/?status=1&parent=&family=&q=&vrf=npflan&mask_length=&export'
        data = urllib.request.urlopen(netbox).read()
        reader = csv.reader(io.StringIO(data.decode()), delimiter=',', quotechar='|')
        subnets = []

        for row in reader:
            if row[7].lower() == "Access".lower() or row[7].lower() == "Wireless".lower() or row[9].lower() == "AP-MGMT".lower():
                if row[9].lower() == 'Wireless Networks'.lower():
                    continue
                # Add networks to array
                subnets.append(IPv4Network(row[0]))
        self.subnets = subnets
        self.leases = IscDhcpLeases(leasefile)
        print("dhcpd_exporter started!")

    def collect(self):
        scope_size = GaugeMetricFamily('size_per_scope', 'Size of scope', labels=['scope'])
        for network in self.subnets:
            scope_size.add_metric([str(network)], network.num_addresses-2)
        yield scope_size

        scope_usage = GaugeMetricFamily('usage_per_scope', 'Currently in use leases per scope', labels=['scope'])
        # TODO: Very bad from a performance perspective, needs optimization
        uses = defaultdict(lambda: 0)
        cur_leases = 0
        total_leases = 0
        for lease in self.leases.get():
            total_leases = total_leases + 1
            if lease.valid and lease.active:
                cur_leases = cur_leases + 1
                parsed = IPv4Address(lease.ip)
                for network in self.subnets:
                    if parsed in network:
                        uses[network] = uses[network] + 1
                        break
        for network, used_ips in uses.items():
            scope_usage.add_metric([str(network)], used_ips)
        yield scope_usage

        yield GaugeMetricFamily('total_current', 'Total amount of current valid leases', value=cur_leases)
        yield GaugeMetricFamily('total_leases', 'Total amount of leases valid and invalid', value=total_leases)
        

# For easy debugging
if __name__ == '__main__':
    print('hello')
    d = DhcpdCollector(leasefile='dhcpd.leases')
    output = []
    for metric in d.collect():
        output.append('# HELP {0} {1}'.format(
            metric.name, metric.documentation.replace('\\', r'\\').replace('\n', r'\n')))
        output.append('\n# TYPE {0} {1}\n'.format(metric.name, metric.type))
        for name, labels, value in metric.samples:
            if labels:
                labelstr = '{{{0}}}'.format(','.join(
                    ['{0}="{1}"'.format(
                     k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
                     for k, v in sorted(labels.items())]))
            else:
                labelstr = ''
            output.append('{0}{1} {2}\n'.format(name, labelstr, value))
    print(''.join(output).encode('utf-8'))

# For running with a wsgi server like gunicorn
REGISTRY.register(DhcpdCollector())
app = prometheus_client.make_wsgi_app()

