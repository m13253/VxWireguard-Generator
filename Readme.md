VxWireguard-Generator
=====================

Utility to generate VXLAN over Wireguard mesh SD-WAN configuration

## Recommendation of RAIT

In case you want a "poor-man's SD-WAN" based on Wireguard and VWGen cannot suit your needs, you may also want to consider [RAIT](https://gitlab.com/NickCao/RAIT).

---

## Setup

Requires: Linux, Python >= 3.7, [toml](https://pypi.org/project/toml/), [PyNaCl](https://pypi.org/project/PyNaCl/)

```bash
sudo pip3 install -r requirements.txt
python3 setup.py build
sudo python3 setup.py install --force
```

## Example

```bash
# Find a good place to store the data
mkdir -p ~/Documents/vwnetworks
cd ~/Documents/vwnetworks

# Add a mesh network
vwgen add wg-meshvpn

# Set the address pool of the network
vwgen set wg-meshvpn pool-ipv4 172.20.10.0/24 pool-ipv6 2001:db8:42::/64

# Add 3 nodes
# They will have IPv4 addresses fixed and IPv6 addresses dynamically calculated on demand
vwgen add wg-meshvpn node1 node2 node3

# Set endpoint of node1 and node2 to their public IP addresses (either IPv4 or IPv6 will work), leave empty for node3 so it will do auto-discovery
vwgen set wg-meshvpn node node1 endpoint '[2001:db8:1::1]:1234' listen-port 1234
vwgen set wg-meshvpn node node2 endpoint '[2001:db8:2::1]:2345' listen-port 2345
vwgen set wg-meshvpn node node3 listen-port 3456

# Show all information we have so far
vwgen show wg-meshvpn

# Generate a configuration for node1
# It's a bad habit to log into server with root, this is just a demo
vwgen showconf wg-meshvpn node1 > node1.conf
scp node1.conf 'root@[2001:db8:1::1]:/etc/wireguard/wg-meshvpn.conf'
ssh root@2001:db8:1::1 chmod 600 /etc/wireguard/wg-meshvpn.conf \; systemctl enable --now wg-quick@wg-meshvpn

# Generate a configuration for node2
vwgen showconf wg-meshvpn node2 > node2.conf
scp node1.conf 'root@[2001:db8:2::1]:/etc/wireguard/wg-meshvpn.conf'
ssh root@2001:db8:2::1 chmod 600 /etc/wireguard/wg-meshvpn.conf \; systemctl enable --now wg-quick@wg-meshvpn

# The configuration is stored in plaintext TOML format
less wg-meshvpn.conf
```

## Routing protocol

Now you have all your nodes on the same virtual Ethernet.

You may run routing protocol designed for mesh networks (e.g.
[Babel](https://github.com/jech/babeld), EIGRP) on interface `vwg-meshvpn` to
announce connected network segments to each other, and to calculate the best
forwarding route between each node.

## Limitations

- The MAC and IPv6 addresses is generated with the last bits from the public key. Currently no duplication detection is performed. It is recommended that you check the addresses yourself, or use DAD to detect duplicates. If a collision is found, please regenerate a new key, or packets will be forwarded to the wrong node.

- The mesh network relies on the fact that every node is in a trusted environment that no one can inject IPv6 ND packets into the backbone network. In other words, do not bridge the backbone network to your customer network. Use routing instead of bridging.

## License

MIT License

Copyright (c) 2018 Star Brilliant

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
