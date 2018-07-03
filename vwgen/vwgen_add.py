#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2018 Star Brilliant
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import binascii
import errno
import ipaddress
import random
import sys
from typing import Any, Dict, List, Optional, Set
from . import common


def main(argv: List[str]) -> int:

    if len(argv) < 3 or argv[2] == '--help':
        print_usage()
        return 0
    network_name = argv[2]
    config = common.Config()
    config.load(network_name)
    network = config.network()
    nodes = config.nodes()
    blacklist = config.blacklist()
    config.save()

    return_value = 0

    for node_name in argv[3:]:
        if node_name in nodes:
            print("vwgen: Network '{}' already has node '{}'".format(network_name, node_name), file=sys.stderr)
            return_value = return_value or errno.EEXIST
            continue

        node: Dict[str, Any] = common.SortedDict()
        if 'AddressPoolIPv4' in network:
            ipv4 = generate_random_ipv4(network, nodes)
            if ipv4 is None:
                print('vwgen: IPv4 address pool is full')
                break
            node['Address'] = [ipv4]
        else:
            node['Address'] = []

        ipv4ll = generate_random_ipv4ll(nodes)
        if ipv4ll is None:
            print('vwgen: Link-layer address pool is full')
            break

        node['AllowedIPs'] = [ipv4ll + '/32']
        node['Endpoint'] = None
        node['FwMark'] = 0
        node['LinkLayerAddress'] = [ipv4ll + '/16']
        node['ListenPort'] = random.randint(32768, 60999)
        node['PersistentKeepalive'] = 0
        node['PrivateKey'] = binascii.b2a_base64(common.genkey(), newline=False).decode('ascii')
        node['SaveConfig'] = False
        node['UPnP'] = False

        node['PreUp'] = []
        node['PostUp'] = []
        node['PreDown'] = []
        node['PostDown'] = []

        nodes[node_name] = node

    config.save()
    config.close()
    return return_value


def print_usage() -> None:
    print('Usage: vwgen add <network> <node> [<node> ...]')


def generate_random_ipv4(network: Dict[str, Any], nodes: Dict[str, dict]) -> Optional[str]:

    address_pool = ipaddress.IPv4Network(network['AddressPoolIPv4'], strict=False)

    if address_pool.prefixlen < 31:
        num_hosts = address_pool.num_addresses - 2
    else:
        num_hosts = address_pool.num_addresses

    existing_addresses: Set[str] = set((str(j).split('/', 1)[0] for i in nodes.values() for j in i.get('Address', [])))

    if len(existing_addresses) == num_hosts:
        return None

    while True:

        if address_pool.prefixlen >= 32:
            host = 0
        elif address_pool.prefixlen == 31:
            host = random.randint(0, 1)
        else:
            host = random.randint(1, (0xffffffff >> address_pool.prefixlen) - 1)

        ipv4 = ipaddress.IPv4Address(int(address_pool.network_address) | host).compressed

        if ipv4 not in existing_addresses:
            break

    return ipv4 + '/' + str(address_pool.prefixlen)


def generate_random_ipv4ll(nodes: Dict[str, dict]) -> Optional[str]:

    existing_addresses: Set[str] = set((str(j).split('/', 1)[0] for i in nodes.values() for j in i.get('LinkLayerAddress', [])))

    if len(existing_addresses) >= 0xa9feff00 - 0xa9fe0100:
        return None

    while True:

        ipv4ll = ipaddress.IPv4Address(random.randint(0xa9fe0100, 0xa9fefeff)).compressed

        if ipv4ll not in existing_addresses:
            break

    return ipv4ll


if __name__ == '__main__':
    sys.exit(main(sys.argv))
