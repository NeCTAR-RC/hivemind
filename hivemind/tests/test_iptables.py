import unittest
import mock

from hivemind import iptables


IPTABLES_OUTPUT = """Chain INPUT (policy ACCEPT)
target     prot opt source               destination
nova-compute-INPUT  all  --  0.0.0.0/0            0.0.0.0/0
nova-network-INPUT  all  --  0.0.0.0/0            0.0.0.0/0
nova-api-metadat-INPUT  all  --  0.0.0.0/0            0.0.0.0/0
NECTAR-ADMIN  all  --  0.0.0.0/0            0.0.0.0/0

Chain FORWARD (policy ACCEPT)
target     prot opt source               destination
nova-filter-top  all  --  0.0.0.0/0            0.0.0.0/0
nova-compute-FORWARD  all  --  0.0.0.0/0            0.0.0.0/0
nova-network-FORWARD  all  --  0.0.0.0/0            0.0.0.0/0
nova-api-metadat-FORWARD  all  --  0.0.0.0/0            0.0.0.0/0

Chain OUTPUT (policy ACCEPT)
target     prot opt source               destination
nova-filter-top  all  --  0.0.0.0/0            0.0.0.0/0
nova-compute-OUTPUT  all  --  0.0.0.0/0            0.0.0.0/0
nova-network-OUTPUT  all  --  0.0.0.0/0            0.0.0.0/0
nova-api-metadat-OUTPUT  all  --  0.0.0.0/0            0.0.0.0/0

Chain LOGDROP (0 references)
target     prot opt source               destination
LOG        all  --  0.0.0.0/0            0.0.0.0/0            limit: avg 10/min burst 7 LOG flags 0 level 4
DROP       all  --  0.0.0.0/0            0.0.0.0/0

Chain LOGREJECT (18 references)
target     prot opt source               destination
LOG        all  --  0.0.0.0/0            0.0.0.0/0            limit: avg 10/min burst 7 LOG flags 0 level 4
REJECT     all  --  0.0.0.0/0            0.0.0.0/0            reject-with icmp-port-unreachable

Chain nova-api-metadat-FORWARD (1 references)
target     prot opt source               destination

Chain nova-api-metadat-INPUT (1 references)
target     prot opt source               destination
ACCEPT     tcp  --  0.0.0.0/0            192.168.1.1        tcp dpt:8775

Chain nova-api-metadat-OUTPUT (1 references)
target     prot opt source               destination

Chain nova-api-metadat-local (1 references)
target     prot opt source               destination

Chain nova-compute-FORWARD (1 references)
target     prot opt source               destination
ACCEPT     udp  --  0.0.0.0              255.255.255.255      udp spt:68 dpt:67

Chain nova-compute-INPUT (1 references)
target     prot opt source               destination
ACCEPT     udp  --  0.0.0.0              255.255.255.255      udp spt:68 dpt:67

Chain nova-compute-OUTPUT (1 references)
target     prot opt source               destination

Chain nova-compute-inst-37779 (1 references)
target     prot opt source               destination
DROP       all  --  0.0.0.0/0            0.0.0.0/0            state INVALID
ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0            state RELATED,ESTABLISHED
nova-compute-provider  all  --  0.0.0.0/0            0.0.0.0/0
ACCEPT     udp  --  213.234.38.24        0.0.0.0/0            udp spt:67 dpt:68
ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:22
nova-compute-sg-fallback  all  --  0.0.0.0/0            0.0.0.0/0

Chain nova-compute-inst-38222 (1 references)
target     prot opt source               destination
DROP       all  --  0.0.0.0/0            0.0.0.0/0            state INVALID
ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0            state RELATED,ESTABLISHED
nova-compute-provider  all  --  0.0.0.0/0            0.0.0.0/0
ACCEPT     udp  --  89.34.3.9        0.0.0.0/0            udp spt:67 dpt:68
ACCEPT     icmp --  0.0.0.0/0            0.0.0.0/0
ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:22
ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:80
ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:443
nova-compute-sg-fallback  all  --  0.0.0.0/0            0.0.0.0/0

Chain nova-network-OUTPUT (1 references)
target     prot opt source               destination

Chain nova-network-local (1 references)
target     prot opt source               destination
"""


class NodeFixture(mock.MagicMock):

    def __init__(self, *args, **kwargs):
        super(NodeFixture, self).__init__(*args, **kwargs)
        self.roledefs = {"nova-node": ["test.home"]}
        self.host_string = "test.home"


class IptablesTestCase(unittest.TestCase):

    @mock.patch('hivemind.iptables.run')
    @mock.patch('hivemind.decorators.env', new_callable=NodeFixture)
    def test_list(self, mock_env, mock_run):
        """Test that the correct packages are parsed out of the apt output."""
        mock_run.return_value = IPTABLES_OUTPUT
        rules = iptables.parse_rules()
        self.assertEqual(
            rules,
            {'37779': [{'destination': '0.0.0.0/0',
                        'filter': 'state INVALID',
                        'options': '--',
                        'protocol': 'all',
                        'source': '0.0.0.0/0',
                        'target': 'DROP'},
                       {'destination': '0.0.0.0/0',
                        'filter': 'state RELATED,ESTABLISHED',
                        'options': '--',
                        'protocol': 'all',
                        'source': '0.0.0.0/0',
                        'target': 'ACCEPT'},
                       {'destination': '0.0.0.0/0',
                        'filter': '',
                        'options': '--',
                        'protocol': 'all',
                        'source': '0.0.0.0/0',
                        'target': 'nova-compute-provider'},
                       {'destination': '0.0.0.0/0',
                        'filter': 'udp spt:67 dpt:68',
                        'options': '--',
                        'protocol': 'udp',
                        'source': '213.234.38.24',
                        'target': 'ACCEPT'},
                       {'destination': '0.0.0.0/0',
                        'filter': 'tcp dpt:22',
                        'options': '--',
                        'protocol': 'tcp',
                        'source': '0.0.0.0/0',
                        'target': 'ACCEPT'},
                       {'destination': '0.0.0.0/0',
                        'filter': '',
                        'options': '--',
                        'protocol': 'all',
                        'source': '0.0.0.0/0',
                        'target': 'nova-compute-sg-fallback'}],
             '38222': [{'destination': '0.0.0.0/0',
                        'filter': 'state INVALID',
                        'options': '--',
                        'protocol': 'all',
                        'source': '0.0.0.0/0',
                        'target': 'DROP'},
                       {'destination': '0.0.0.0/0',
                        'filter': 'state RELATED,ESTABLISHED',
                        'options': '--',
                        'protocol': 'all',
                        'source': '0.0.0.0/0',
                        'target': 'ACCEPT'},
                       {'destination': '0.0.0.0/0',
                        'filter': '',
                        'options': '--',
                        'protocol': 'all',
                        'source': '0.0.0.0/0',
                        'target': 'nova-compute-provider'},
                       {'destination': '0.0.0.0/0',
                        'filter': 'udp spt:67 dpt:68',
                        'options': '--',
                        'protocol': 'udp',
                        'source': '89.34.3.9',
                        'target': 'ACCEPT'},
                       {'destination': '0.0.0.0/0',
                        'filter': '',
                        'options': '--',
                        'protocol': 'icmp',
                        'source': '0.0.0.0/0',
                        'target': 'ACCEPT'},
                       {'destination': '0.0.0.0/0',
                        'filter': 'tcp dpt:22',
                        'options': '--',
                        'protocol': 'tcp',
                        'source': '0.0.0.0/0',
                        'target': 'ACCEPT'},
                       {'destination': '0.0.0.0/0',
                        'filter': 'tcp dpt:80',
                        'options': '--',
                        'protocol': 'tcp',
                        'source': '0.0.0.0/0',
                        'target': 'ACCEPT'},
                       {'destination': '0.0.0.0/0',
                        'filter': 'tcp dpt:443',
                        'options': '--',
                        'protocol': 'tcp',
                        'source': '0.0.0.0/0',
                        'target': 'ACCEPT'},
                       {'destination': '0.0.0.0/0',
                        'filter': '',
                        'options': '--',
                        'protocol': 'all',
                        'source': '0.0.0.0/0',
                        'target': 'nova-compute-sg-fallback'}]})
