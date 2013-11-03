import unittest
import mock
from hivemind import apt


class NodeFixture(mock.MagicMock):

    def __init__(self, *args, **kwargs):
        super(NodeFixture, self).__init__(*args, **kwargs)
        self.roledefs = {"nova-node": ["test.home"]}
        self.host_string = "test.home"


APT_DIST_UPGRADE_OUTPUT = """Reading package lists... Done
Building dependency tree
Reading state information... Done
Calculating upgrade... Done
The following NEW packages will be installed:
   linux-headers-3.2.0-55 (3.2.0-55.85)
   linux-headers-3.2.0-55-generic (3.2.0-55.85)
   linux-image-3.2.0-55-generic (3.2.0-55.85)
   python-d2to1 (0.2.10-1ubuntu4~cloud0)
   python-dnspython (1.11.0-1~cloud0)
   python-netaddr (0.7.7-1~cloud0)
   python-pbr (0.5.21-0ubuntu4~cloud0)
The following packages will be upgraded:
   linux-generic (3.2.0.53.63 => 3.2.0.55.65)
   linux-headers-generic (3.2.0.53.63 => 3.2.0.55.65)
   linux-image-generic (3.2.0.53.63 => 3.2.0.55.65)
   python-keystoneclient (0.2.3-1nectar8 => 0.3.2-0ubuntu1~cloud0)
   python-swift (1.8.0-0ubuntu1.2~cloud0 => 1.10.0-0ubuntu1~cloud0)
   python-swiftclient (1.3.0-0ubuntu1~cloud0 => 1.6.0-0ubuntu1~cloud0)
   swift (1.8.0-0ubuntu1.2~cloud0 => 1.10.0-0ubuntu1~cloud0)
   swift-account (1.8.0-0ubuntu1.2~cloud0 => 1.10.0-0ubuntu1~cloud0)
   swift-container (1.8.0-0ubuntu1.2~cloud0 => 1.10.0-0ubuntu1~cloud0)
   swift-object (1.8.0-0ubuntu1.2~cloud0 => 1.10.0-0ubuntu1~cloud0)
10 upgraded, 7 newly installed, 0 to remove and 0 not upgraded.
"""


class AptTestCase(unittest.TestCase):

    @mock.patch('hivemind.apt.run')
    @mock.patch('hivemind.decorators.env', new_callable=NodeFixture)
    def test_verify(self, mock_env, mock_run):
        """Test that the correct packages are parsed out of the apt output."""
        mock_run.return_value = APT_DIST_UPGRADE_OUTPUT
        upgradables = apt.verify()
        self.assertEqual(
            upgradables,
            {'linux-generic': ('3.2.0.53.63',
                               '3.2.0.55.65'),
             'swift-account': ('1.8.0-0ubuntu1.2~cloud0',
                               '1.10.0-0ubuntu1~cloud0'),
             'python-d2to1': ('not currently installed',
                              '0.2.10-1ubuntu4~cloud0'),
             'python-swift': ('1.8.0-0ubuntu1.2~cloud0',
                              '1.10.0-0ubuntu1~cloud0'),
             'swift-object': ('1.8.0-0ubuntu1.2~cloud0',
                              '1.10.0-0ubuntu1~cloud0'),
             'linux-headers-3.2.0-55': ('not currently installed',
                                        '3.2.0-55.85'),
             'python-netaddr': ('not currently installed',
                                '0.7.7-1~cloud0'),
             'linux-image-generic': ('3.2.0.53.63',
                                     '3.2.0.55.65'),
             'python-dnspython': ('not currently installed',
                                  '1.11.0-1~cloud0'),
             'linux-image-3.2.0-55-generic': ('not currently installed',
                                              '3.2.0-55.85'),
             'linux-headers-generic': ('3.2.0.53.63',
                                       '3.2.0.55.65'),
             'python-keystoneclient': ('0.2.3-1nectar8',
                                       '0.3.2-0ubuntu1~cloud0'),
             'swift-container': ('1.8.0-0ubuntu1.2~cloud0',
                                 '1.10.0-0ubuntu1~cloud0'),
             'linux-headers-3.2.0-55-generic': ('not currently installed',
                                                '3.2.0-55.85'),
             'python-swiftclient': ('1.3.0-0ubuntu1~cloud0',
                                    '1.6.0-0ubuntu1~cloud0'),
             'swift': ('1.8.0-0ubuntu1.2~cloud0', '1.10.0-0ubuntu1~cloud0'),
             'python-pbr': ('not currently installed',
                            '0.5.21-0ubuntu4~cloud0')})
