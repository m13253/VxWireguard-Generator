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
import importlib
import nacl
import sys
import toml
import typing


def main(argv: typing.List[str]) -> int:
    if len(argv) < 2 or argv[1] == '--help':
        print_help(argv[0])
        return 0
    try:
        submodule: typing.Any = importlib.import_module('.vwgen_' + argv[1], 'vwgen')
    except ImportError:
        print("vwgen: Invalid command '{}'".format(argv[1]), file=sys.stderr)
        return errno.ENOENT
    submodule.main(argv)
    return 0


def print_help(program_name: str) -> None:
    print('Usage vwgen <cmd> [<args>]')
    print()
    print('Available subcommands')
    print('  show: Shows the current configuration of the mesh network')
    print('  showconf: Generate a configuration file for a given node')
    print('  add: Add new nodes to the mesh network')
    print('  set: Change the configuration of nodes')
    print('  del: Delete nodes from the mesh network')
    print('  blacklist: Manage peering blacklist between specified nodes')
    print('  zone: Generate BIND-style DNS zone records')
    print('  genkey: Generates a new private key and writes it to stdout')
    print('  genpsk: Generates a new preshared key and writes it to stdout')
    print('  pubkey: Reads a private key from stdin and writes a public key to stdout')
    print("You may pass '--help' to any of these subcommands to view usage.")


if __name__ == '__main__':
    sys.exit(main(sys.argv))
