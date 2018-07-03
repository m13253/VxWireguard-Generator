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
import random
import sys
from typing import List
from . import common


def main(argv: List[str]) -> int:

    if len(argv) < 4 or argv[2] == '--help':
        print_usage()
        return 0

    network_name = argv[2]
    config = common.Config()

    if not config.load(network_name):
        print("vwgen: Unable to find configuration file '{}.conf'".format(network_name), file=sys.stderr)
        return errno.ENOENT

    network = config.network()
    nodes = config.nodes()
    blacklist = config.blacklist()
    config.save()

    return_value = 0

    for node_name in argv[3:]:
        if node_name not in nodes:
            print("vwgen: Network '{}' does not have node '{}'".format(network_name, node_name), file=sys.stderr)
            return_value = return_value or errno.ENOENT
            continue
        del nodes[node_name]

        for i in blacklist:
            if node_name in i:
                blacklist.remove(i)

    config.save()
    config.close()
    return return_value


def print_usage() -> None:
    print('Usage: vwgen del <network> <node> [<node> ...]')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
