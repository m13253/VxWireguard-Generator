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

import pudb
import binascii
import collections
import errno
import fcntl
import ipaddress
import nacl.bindings
import random
import sys
import toml
from typing import Any, Callable, cast, Dict, Generic, ItemsView, Iterable, Iterator, KeysView, List, Optional, Set, TextIO, Tuple, TypeVar, ValuesView

T = TypeVar('T')
KT = TypeVar('KT')
VT = TypeVar('VT')


# This metaclass patches the type check of toml 0.9.x
# It should use isinstance(v, list), but actually uses type(v) == list instead
class _FakeListMeta(type(list)):  # type: ignore
    def __hash__(self) -> int:
        return hash(list)

    def __eq__(self, other: Any) -> bool:
        return id(self) == id(other) or id(list) == id(other)

    def __ne__(self, other: Any) -> bool:
        return id(self) != id(other) and id(list) != id(other)


class SortedDict(dict, Generic[KT, VT]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def keys(self) -> KeysView[KT]:
        return cast(KeysView[KT], sorted(super().keys()))

    def values(self) -> ValuesView[VT]:
        return super().values()

    def items(self) -> ItemsView[KT, VT]:
        return cast(ItemsView[KT, VT], sorted(super().items()))

    def __iter__(self) -> Iterator[KT]:
        return iter(self.keys())

    def __repr__(self) -> str:
        return '{' + ', '.join((repr(k) + ': ' + repr(v) for k, v in self.items())) + '}'

    def __str__(self) -> str:
        return repr(self)


class SortedSet(list, Generic[T], metaclass=_FakeListMeta):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._set: Set[T] = set(*args, **kwargs)
        self._sorted: bool = False
        super().__init__()

    def add(self, item: T) -> None:
        self._set.add(item)
        self._sorted = False

    def remove(self, item: T) -> None:
        self._set.remove(item)
        self._sorted = False

    def sort(self, **kwargs: Any) -> None:
        if not self._sorted:
            super().__init__(self._set)
            super().sort(**kwargs)
            self._sorted = True

    def __contains__(self, key: Any) -> bool:
        return key in self._set

    def __iter__(self) -> Iterator[T]:
        self.sort()
        return super().__iter__()

    def __len__(self) -> int:
        return len(self._set)

    def __repr__(self) -> str:
        return '{' + ', '.join((repr(i) for i in self)) + '}'

    def __str__(self) -> str:
        return repr(self)


class NamePair(list, metaclass=_FakeListMeta):
    def __init__(self, name1: str, name2: str) -> None:
        super().__init__((name1, name2))

    def __hash__(self) -> int:
        return hash(tuple(self))


class Config:
    def __init__(self) -> None:
        self._conf: dict = SortedDict()
        self._conf_file: Optional[TextIO] = None
        self._conf_name: Optional[str] = None
        self._writable: bool = False

    def __del__(self) -> None:
        try:
            self._close_file()
        except Exception:
            pass

    def load(self, conf_name: str) -> bool:
        if conf_name.endswith('.conf'):
            conf_name = conf_name[:-5]
        try:
            self._open_file(conf_name)
        except FileNotFoundError:
            self._conf = SortedDict()
            self._conf_name = conf_name
            return False
        self._conf = toml.load(self._conf_file, SortedDict)
        return True

    def save(self) -> None:
        if self._conf is None:
            return
        elif self._conf_name is None:
            return
        self._open_file(self._conf_name, writable=True)
        assert self._conf_file is not None
        data: str = toml.dumps(self._conf)
        self._conf_file.truncate()
        self._conf_file.write(data)

    def close(self) -> None:
        self._close_file()

    def network_name(self) -> str:
        if self._conf_name is None:
            raise ValueError('Config not loaded')
        return self._conf_name

    def network(self) -> Dict[str, Any]:
        if 'Network' not in self._conf:
            self._conf['Network'] = SortedDict[str, Any]()
            self._conf['Network']['AddressPoolIPv4'] = '192.168.{}.0/24'.format(random.randint(2, 255))
            self._conf['Network']['AddressPoolIPv6'] = '{:x}:{:x}:{:x}::/80'.format(random.randint(0xfd00, 0xfdff), random.randint(0x1000, 0xffff), random.randint(0x1000, 0xffff))
            self._conf['Network']['VxlanAddress'] = str(ipaddress.IPv4Address(random.randint(0xe0000100, 0xefffffff)))
            self._conf['Network']['VxlanID'] = random.randint(1, 0xffffff)
            # To make a UDP packet 2048 byte so we don't waste too many bytes transmitting fragmented headers
            self._conf['Network']['VxlanMTU'] = 1966
            self._conf['Network']['VxlanPort'] = 4789
        return cast(SortedDict[str, Any], self._conf['Network'])

    def nodes(self) -> Dict[str, Dict[str, Any]]:
        if 'Node' not in self._conf:
            self._conf['Node'] = SortedDict()
        return cast(SortedDict[str, Dict[str, Any]], self._conf['Node'])

    def blacklist(self) -> SortedSet[NamePair]:
        if 'PeerBlacklist' not in self._conf:
            self._conf['PeerBlacklist'] = {'Blacklist': SortedSet()}
        elif 'Blacklist' not in self._conf['PeerBlacklist']:
            self._conf['PeerBlacklist']['Blacklist'] = SortedSet()
        elif not isinstance(self._conf['PeerBlacklist']['Blacklist'], SortedSet):
            self._conf['PeerBlacklist']['Blacklist'] = SortedSet((NamePair(i, j) for i, j in self._conf['PeerBlacklist']['Blacklist']))
        return cast(SortedSet[NamePair], self._conf['PeerBlacklist']['Blacklist'])

    def _close_file(self) -> None:
        if self._conf_file is None:
            return
        fcntl.lockf(self._conf_file, fcntl.LOCK_UN)
        self._conf_file.close()
        self._conf_file = None

    def _open_file(self, conf_name: str, writable: bool = False) -> None:
        if self._conf_file is not None and self._conf_name == conf_name and self._writable >= writable:
            self._conf_file.seek(0)
            return
        self._close_file()
        if writable:
            conf_file = open(conf_name + '.conf', 'w+')
        else:
            conf_file = open(conf_name + '.conf', 'r')
        try:
            try:
                if writable:
                    fcntl.lockf(conf_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:
                    fcntl.lockf(conf_file, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except OSError as e:
                if e.errno in (errno.EACCES, errno.EAGAIN):
                    print('The configuration file is being used by another process, waiting.', end='', file=sys.stderr, flush=True)
                    if writable:
                        fcntl.lockf(conf_file, fcntl.LOCK_EX)
                    else:
                        fcntl.lockf(conf_file, fcntl.LOCK_SH)
                    print(file=sys.stderr, flush=True)
                else:
                    raise
        except Exception as e:
            conf_file.close()
            raise
        self._conf_file = conf_file
        self._conf_name = conf_name
        self._writable = writable


def genpsk() -> bytes:
    return cast(bytes, nacl.bindings.randombytes(32))


def genkey() -> bytes:
    secret = bytearray(nacl.bindings.randombytes(32))
    # curve25519_normalize_secret
    secret[0] &= 248
    secret[31] &= 127
    secret[31] |= 64
    return bytes(secret)


def pubkey(secret: bytes) -> bytes:
    return cast(bytes, nacl.bindings.crypto_scalarmult_base(secret))


def generate_pubkey_macaddr(node: dict) -> Optional[str]:

    if 'PrivateKey' not in node:
        return None
    secret_base64: str = node['PrivateKey']
    secret: bytes = binascii.a2b_base64(secret_base64)
    if len(secret) != 32:
        return None

    macaddr = pubkey(secret)[-6:]
    return '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format((macaddr[0] & 0xfe) | 0x02, macaddr[1], macaddr[2], macaddr[3], macaddr[4], macaddr[5])


def generate_pubkey_ipv6(network: Dict[str, Any], node: dict) -> Optional[str]:

    if 'AddressPoolIPv6' not in network:
        return None
    address_pool = ipaddress.IPv6Network(network['AddressPoolIPv6'], strict=False)

    if 'PrivateKey' not in node:
        return None
    secret_base64: str = node['PrivateKey']
    secret: bytes = binascii.a2b_base64(secret_base64)
    if len(secret) != 32:
        return None

    host = ipaddress.IPv6Address(pubkey(secret)[-16:])
    ipv6 = ipaddress.IPv6Address(int(address_pool.network_address) | (int(host) & int(address_pool.hostmask)))

    return ipv6.compressed + '/' + str(address_pool.prefixlen)
