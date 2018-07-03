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
from typing import cast, List, Optional, Set, Tuple
from . import common


def main(argv: List[str]) -> int:

    if len(argv) < 6 or argv[2] == '--help':
        print_usage()
        return 0
    network_name = argv[2]
    config = common.Config()
    config.load(network_name)
    network = config.network()
    nodes = config.nodes()
    blacklist = config.blacklist()
    config.save()

    operation: Optional[bool] = None
    if 'add'.startswith(argv[3]):
        operation = True
    elif 'delete'.startswith(argv[3]):
        operation = False
    else:
        print("vwgen: Invalid operation '{}'".format(argv[3]))
        return errno.EINVAL

    return_value = 0

    left_node = argv[4]
    if left_node not in nodes:
        print("vwgen: Network '{}' does not have node '{}'".format(network_name, left_node), file=sys.stderr)
        return_value = return_value or errno.ENOENT
        if operation:
            return return_value

    for right_node in argv[5:]:

        if right_node not in nodes:
            print("vwgen: Network '{}' does not have node '{}'".format(network_name, right_node), file=sys.stderr)
            return_value = return_value or errno.ENOENT
            if operation:
                continue

        if operation:
            blacklist.add(common.NamePair(left_node, right_node))
            blacklist.add(common.NamePair(right_node, left_node))
        else:
            try:
                blacklist.remove(common.NamePair(left_node, right_node))
            except KeyError:
                pass
            try:
                blacklist.remove(common.NamePair(right_node, left_node))
            except KeyError:
                pass

    config.save()
    config.close()
    return return_value


def print_usage() -> None:
    print('Usage: vwgen blacklist <network> <add | del> <left_node> <right_node> [<right_node> ...]')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
