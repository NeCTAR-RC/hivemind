from fabric.api import hide, run
import email


def get_package(package):
    with hide("everything"):
        res = run("dpkg -s {0}".format(package))
    return email.message_from_string(res)


def current_version(package):
    package = get_package(package)
    if package["Status"] == "install ok installed":
        return package["Version"]


def current_versions(package):
    if isinstance(package, list):
        package = " ".join(package)
    with hide("everything"):
        res = run("dpkg -l {0}".format(package))
    return res
