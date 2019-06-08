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

import errno
import ipaddress
import sys
from typing import List, Optional
from . import common


class InvalidNodeError(Exception):
    pass


def main(argv: List[str]) -> int:
    if len(argv) < 3 or argv[2] == '--help':
        print_usage()
        return 0

    network_name = argv[2]
    config = common.Config()

    if not config.load(network_name):
        print("vwgen: Unable to find configuration file '{}.conf'".format(network_name), file=sys.stderr)
        return errno.ENOENT

    network = config.network()
    nodes = config.nodes()
    node: Optional[common.Config.NodeType] = None
    config.save()

    arg_index = 3
    return_value = 0

    try:
        while arg_index < len(argv):

            if argv[arg_index] == 'node':
                node_name = argv[arg_index + 1]
                if node_name not in nodes:
                    print("vwgen: Network '{}' does not have node '{}'".format(network_name, node_name), file=sys.stderr)
                    return errno.ENOENT
                node = nodes[node_name]
                arg_index += 2

            elif argv[arg_index] == 'pool-ipv4':
                network['AddressPoolIPv4'] = ipaddress.IPv4Network(argv[arg_index + 1], strict=False).compressed
                arg_index += 2

            elif argv[arg_index] == 'pool-ipv6':
                network['AddressPoolIPv6'] = ipaddress.IPv6Network(argv[arg_index + 1], strict=False).compressed
                arg_index += 2

            elif argv[arg_index] == 'vxlan-id':
                network['VxlanID'] = int(argv[arg_index + 1])
                arg_index += 2

            elif argv[arg_index] == 'vxlan-mtu':
                network['VxlanMTU'] = int(argv[arg_index + 1])
                arg_index += 2

            elif argv[arg_index] == 'vxlan-port':
                network['VxlanPort'] = int(argv[arg_index + 1])
                arg_index += 2

            elif argv[arg_index] == 'addr':
                if node is None:
                    raise InvalidNodeError
                node['Address'] = list(map(str.strip, argv[arg_index + 1].split(',')))
                arg_index += 2

            elif argv[arg_index] == 'allowed-ips':
                if node is None:
                    raise InvalidNodeError
                node['AllowedIPs'] = list(map(str.strip, argv[arg_index + 1].split(',')))
                arg_index += 2

            elif argv[arg_index] == 'endpoint':
                if node is None:
                    raise InvalidNodeError
                if argv[arg_index + 1]:
                    endpoint = argv[arg_index + 1]
                    if endpoint.startswith('[') and endpoint.endswith(']'):
                        endpoint += str(node.get('ListenPort', 0))
                    elif ':' not in endpoint:
                        endpoint += ':' + str(node.get('ListenPort', 0))
                    elif endpoint.count(':') > 1:
                        endpoint = '[' + endpoint + ']:' + str(node.get('ListenPort', 0))
                    node['Endpoint'] = endpoint
                else:
                    node['Endpoint'] = None
                arg_index += 2

            elif argv[arg_index] == 'fwmark':
                if node is None:
                    raise InvalidNodeError
                if argv[arg_index + 1] == 'off':
                    node['FwMark'] = 0
                else:
                    node['FwMark'] = int(argv[arg_index + 1], base=0)
                arg_index += 2

            elif argv[arg_index] == 'll-addr':
                if node is None:
                    raise InvalidNodeError
                node['LinkLayerAddr'] = argv[arg_index + 1]
                arg_index += 2

            elif argv[arg_index] == 'listen-port':
                if node is None:
                    raise InvalidNodeError
                node['ListenPort'] = int(argv[arg_index + 1])
                arg_index += 2

            elif argv[arg_index] == 'persistent-keepalive':
                if node is None:
                    raise InvalidNodeError
                if argv[arg_index + 1] == 'off':
                    node['PersistentKeepalive'] = 0
                else:
                    node['PersistentKeepalive'] = int(argv[arg_index + 1])
                arg_index += 2

            elif argv[arg_index] == 'private-key':
                if node is None:
                    raise InvalidNodeError
                node['PrivateKey'] = argv[arg_index + 1]
                arg_index += 2

            elif argv[arg_index] == 'save-config':
                if node is None:
                    raise InvalidNodeError
                node['SaveConfig'] = True
                arg_index += 1
            elif argv[arg_index] == 'nosave-config':
                if node is None:
                    raise InvalidNodeError
                node['SaveConfig'] = False
                arg_index += 1

            elif argv[arg_index] == 'upnp':
                if node is None:
                    raise InvalidNodeError
                node['UPnP'] = True
                arg_index += 1
            elif argv[arg_index] == 'noupnp':
                if node is None:
                    raise InvalidNodeError
                node['UPnP'] = False
                arg_index += 1

            else:
                print("vwgen: Invalid directive '{}'".format(argv[arg_index]))
                return errno.EINVAL

    except IndexError:
        print("vwgen: Argument not complete, use '--help' to check for help", file=sys.stderr)
    except InvalidNodeError:
        print("vwgen: '{}' must be used after 'node' directive, use '--help' to check for help".format(argv[arg_index]), file=sys.stderr)

    config.save()
    config.close()
    return return_value


def print_usage() -> None:
    print('Usage: vwgen set <network> [pool-ipv4 <ipv4/cidr>] [pool-ipv6 <ipv6/cidr>]')
    print('                           [vxlan-id <vxlan-id>] [vxlan-mtu <vxlan-mtu>]')
    print('                           [vxlan-port <vxlan-port>]')
    print('         [node <node name> [addr <ip1/cidr1>[,<ip2/cidr2>]...]')
    print('                           [allowed-ips <ip1/cidr1>[,<ip2/cidr2>]...]')
    print('                           [endpoint <ip>:<port>] [fwmark <mark>]')
    print('                           [ll-addr <ipv4/cidr>] [listen-port <port>]')
    print('                           [persistent-keepalive <interval seconds>]')
    print('                           [private-key <file path>] [[no]save-config]')
    print('                           [[no]upnp ]')
    print('         [node <node name> ...]')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
