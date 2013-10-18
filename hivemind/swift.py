from operations import run
from fabric.api import parallel, puts, env, shell_env
from fabric.colors import red, blue
from fabric.operations import reboot
from hivemind import util, puppet


@parallel(pool_size=5)
def list_service():

    cmd_output = run("swift-init all status", warn_only=True, quiet=True)
    running_services = []
    disabled_services = []
    get_services = [line for line in cmd_output.split("\n")]
    services_run = [rs for rs in get_services if "No" not in rs]
    for s in services_run:
        running_services.append(s.split()[0])

    services_no = [ds for ds in get_services if "No" in ds]
    for s in services_no:
        disabled_services.append(s.split()[1])

    return running_services, disabled_services


@parallel(pool_size=5)
def stop_services(action=None):

    services = identify_role_service()
    if 'swift-proxy' in services:
        run("swift-init proxy-server stop",
            warn_only=True, quiet=True
            )
    else:
        if action is 'all':
            run("swift-init all stop",
                warn_only=True, quiet=True
                )
        else:
            run("swift-init account-replicator stop")
            run("swift-init account-reaper stop")
            run("swift-init account-auditor stop")
            run("swift-init object-replicator stop")
            run("swift-init object-auditor stop")
            run("swift-init object-updater stop")
            run("swift-init container-replicator stop")
            run("swift-init container-updater stop")
            run("swift-init container-auditor stop")

    return


@parallel(pool_size=5)
def start_services():
    services = identify_role_service()
    if 'swift-proxy' in services:
        cmd_output = run("swift-init proxy-server start",
                         warn_only=True, quiet=True
                         )
    else:
        cmd_output = run("swift-init all start",
                         warn_only=True, quiet=True)

    return cmd_output


def print_results(services):
    print services
    p = lambda x: "\n ".join(x)
    for k, v in services.iteritems():
        if len(v[0])is 0:
            puts("[%s]\n %s\n %s" % (k, blue("=> running"), "None"))
        else:
            puts("[%s]\n %s\n %s" % (k, blue("=> running"), p(set(v[0]))))
        puts("[%s]\n %s\n %s" % (k,  red("=> disabled"), p(set(v[1]))))


@parallel(pool_size=5)
def upgrade(packages=[], nagios=None):
    services = {}
    outage = "Package Upgrade (%s@%s)." % (util.local_user(),
                                           util.local_host())

    if isinstance(packages, dict):
        packages = packages[env.host_string]
    if not packages:
        return
    if nagios is not None:
        nagios.ensure_host_maintence(outage)
    # stop the puppet service, run puppet using agent

    puppet.disable_service()
    backup_ring()
    stop_services()
    puppet.run_agent()
    call_upgrade(packages)
    start_services()
    puppet.enable_service()
    reboot_swift()

    if 'swift-node' in identify_role_service():
        start_services()
    services[env.host_string] = list_service()
    print_results(services)
    if nagios is not None:
        nagios.ensure_host_maintence(outage)


def identify_role_service():
    if len(util.roles()) is 0:
        service = [k for k, v in util.roledefs().items()
                   if util.current_host() in v
                   ]
    else:
        service = "".join(util.roles())

    return service


def call_upgrade(packages):
    with shell_env(DEBIAN_FRONTEND='non-interactive'):
            run("apt-get install -o Dpkg::Options::='--force-confold' %s" %
                " ".join(packages)
                )


def reboot_swift():
    reboot(wait=120)


def backup_ring():
    services = identify_role_service()

    run("mkdir -p /etc/swift/backup_upgrade")
    run("cp /etc/swift/***.ring.gz /etc/swift/backup_upgrade/")

    if 'swift-proxy' in services:
        run("cp /etc/swift/***.builder /etc/swift/backup_upgrade/",
            warn_only=True, quiet=True)
