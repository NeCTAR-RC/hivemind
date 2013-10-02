import mox
from hivemind import nova
import hivemind.decorators


NOVA_MANAGE_OUTPUT = """Binary           Host                                 Zone             Status     State Updated_At
nova-compute     cc4                                  melbourne-local  enabled    XXX   2013-08-23 01:04:08
nova-network     cc4                                  internal         enabled    XXX   2013-08-23 01:04:09
nova-compute     cc2                                  melbourne-shared enabled    :-)   2013-10-02 03:46:52
nova-network     cc2                                  internal         enabled    :-)   2013-10-02 03:46:49
nova-network     cc3                                  internal         enabled    :-)   2013-10-02 03:46:43
nova-compute     cc3                                  melbourne-local  enabled    :-)   2013-10-02 03:46:44
nova-compute     test                                 melbourne-shared enabled    :-)   2013-10-02 03:46:43
nova-network     test                                 internal         enabled    :-)   2013-10-02 03:46:52
nova-consoleauth nova-qh2                             internal         enabled    :-)   2013-10-02 03:46:52
nova-cells       nova-qh2                             internal         enabled    :-)   2013-10-02 03:46:43
nova-scheduler   nova-qh2                             internal         enabled    :-)   2013-10-02 03:46:48"""


class NovaTestCase(mox.MoxTestBase):

    def test_disable_host_services(self):
        """Test disabling the services on a nova host."""
        # Mock out the fabric env dict.
        self.mox.StubOutWithMock(hivemind.decorators, "env")
        mockEnv = hivemind.decorators.env
        mockEnv.roledefs = {"nova-node": ["test.home"]}
        mockEnv.host_string = "test.home"

        # Expected commands to be run to disable the host
        self.mox.StubOutWithMock(nova, "run")
        nova.run('nova-manage service list 2>/dev/null').AndReturn(NOVA_MANAGE_OUTPUT)
        nova.run('nova-manage service disable --host test --service nova-compute').AndReturn("")
        nova.run('nova-manage service disable --host test --service nova-network').AndReturn("")

        self.mox.ReplayAll()

        nova.disable_host_services("test")

        self.mox.VerifyAll()

    def test_disable_host_services_current_host(self):
        """Test disabling the services on a nova host."""
        # Mock out the fabric env dict.
        self.mox.StubOutWithMock(hivemind.decorators, "env")
        mockEnv = hivemind.decorators.env
        mockEnv.roledefs = {"nova-node": ["test.home"]}
        mockEnv.host_string = "test.home"
        self.mox.StubOutWithMock(hivemind.util, "env")
        hivemind.util.env.host_string = "test.home"

        # Expected commands to be run to disable the host
        self.mox.StubOutWithMock(nova, "run")
        nova.run('nova-manage service list 2>/dev/null').AndReturn(NOVA_MANAGE_OUTPUT)
        nova.run('nova-manage service disable --host test --service nova-compute').AndReturn("")
        nova.run('nova-manage service disable --host test --service nova-network').AndReturn("")

        self.mox.ReplayAll()

        nova.disable_host_services()

        self.mox.VerifyAll()

    def test_disable_host_services_no_service(self):
        """Test disabling the services on a host that isn't listed in the the
        nova manage command.

        """
        # Mock out the fabric env dict
        self.mox.StubOutWithMock(hivemind.decorators, "env")
        mockEnv = hivemind.decorators.env
        mockEnv.roledefs = {"nova-node": ["test.home", "banana.home"]}
        mockEnv.host_string = "banana.home"

        # Expected commands to be run
        self.mox.StubOutWithMock(nova, "run")
        nova.run('nova-manage service list 2>/dev/null').AndReturn(NOVA_MANAGE_OUTPUT)

        self.mox.ReplayAll()

        nova.disable_host_services("banana")

        self.mox.VerifyAll()
