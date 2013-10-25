import mox
from hivemind import puppet
import hivemind.decorators


class PuppetTestCase(mox.MoxTestBase):

    def test_disable_host_services(self):
        """Test disabling puppet agent."""
        # Mock out the fabric env dict.
        self.mox.StubOutWithMock(hivemind.decorators, "env")
        mockEnv = hivemind.decorators.env
        mockEnv.roledefs = {"nova-node": ["test.home"]}
        mockEnv.host_string = "test.home"

        # Expected commands to be run to disable the host
        self.mox.StubOutWithMock(puppet, "run")
        puppet.run("puppet agent --disable 'Upgrade'").AndReturn("")
        puppet.run('test').AndReturn("")
        puppet.run('puppet agent --enable').AndReturn("")

        self.mox.ReplayAll()

        with puppet.disabled("Upgrade"):
            puppet.run("test")

        self.mox.VerifyAll()
