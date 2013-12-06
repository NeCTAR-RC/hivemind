import re
from itertools import chain
from collections import defaultdict

from prettytable import PrettyTable
from fabric.api import task, puts, execute, env
from fabric.utils import error

from hivemind.operations import run
from hivemind.nova import client
from hivemind.libvirt import list_instances

comput_rule_re = re.compile("^Chain nova-compute-inst-(\d+) ")


def parse_rules():
    output = run("iptables -n -L")
    instance_id = None
    in_host_rules = False
    host_rules = defaultdict(list)

    for line in output.split('\n'):
        match = comput_rule_re.match(line)
        if match:
            instance_id = match.groups()[0]
            in_host_rules = True
            continue
        if not in_host_rules:
            continue
        columns = line.split()
        # Reset back to default state if no longer parsing an
        # instances firewall.
        if not columns:
            in_host_rules = False
            instance_id = None
            continue

        # Skip the column headers
        if columns[0] == 'target':
            continue
        rule = {'target': columns[0],
                'protocol': columns[1],
                'options': columns[2],
                'source': columns[3],
                'destination': columns[4],
                'filter': ' '.join(columns[5:])}
        host_rules[instance_id].append(rule)
    return host_rules


@task
def vm_rules():
    if not env.instance_uuid:
        error("No instance_uuid specified.")
    uuid = env.instance_uuid
    nova_client = client()
    server = nova_client.servers.get(uuid)
    host = getattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname')
    libvirt_server = [s for s in chain(*execute(list_instances,
                                                host=host).values())
                      if s['uuid'] == uuid][0]
    for vm, rules in chain.from_iterable(map(dict.items,
                                             execute(parse_rules,
                                                     host=host).values())):
        if vm != str(libvirt_server['nova_id']):
            continue
        table = PrettyTable(['Target', 'Protocol', 'Source',
                             'Destination', 'Filter'])
        for rule in rules:
            table.add_row([rule['target'], rule['protocol'], rule['source'],
                           rule['destination'], rule['filter']])
        puts("\n%s\n%s\n" % (server.id, str(table)))
