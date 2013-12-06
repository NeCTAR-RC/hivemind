#!/bin/bash

set -e

function usage {
    echo "Usage: $0 [OPTION]..."
    echo "Run Hiveminds's test suite(s)"
    echo ""
    echo "  -V, --virtual-env           Always use virtualenv.  Install automatically if not present"
    echo "  -N, --no-virtual-env        Don't use virtualenv.  Run tests in local environment"
    echo "  -s, --no-site-packages      Isolate the virtualenv from the global Python environment"
    echo "  -f, --force                 Force a clean re-build of the virtual environment. Useful when dependencies have been added."
    echo "  -u, --update                Update the virtual environment with any newer package versions"
    echo "  -h, --help                  Print this usage message"
    echo "  --virtual-env-path <path>   Location of the virtualenv directory"
    echo "                               Default: \$(pwd)"
    echo "  --virtual-env-name <name>   Name of the virtualenv directory"
    echo "                               Default: .venv"
    echo ""
    echo "Note: with no options specified, the script will try to run the tests in a virtual environment,"
    echo "      If no virtualenv is found, the script will ask if you would like to create one.  If you "
    echo "      prefer to run tests NOT in a virtual environment, simply pass the -N option."
    exit
}

function process_options {
    i=1
    while [ $i -le $# ]; do
        case "${!i}" in
            -h|--help) usage;;
            -V|--virtual-env) always_venv=1; never_venv=0;;
            -N|--no-virtual-env) always_venv=0; never_venv=1;;
            -s|--no-site-packages) no_site_packages=1;;
            -f|--force) force=1;;
            -u|--update) update=1;;
            --virtual-env-path)
                (( i++ ))
                venv_path=${!i}
                ;;
            --virtual-env-name)
                (( i++ ))
                venv_dir=${!i}
                ;;
        esac
        (( i++ ))
    done
}

venv_path=${venv_path:-$(pwd)}
venv_dir=${venv_name:-.venv}
always_venv=0
never_venv=0
force=0
update=0
no_site_packages=0
installvenvopts=

process_options $@

export venv=${venv_path}/${venv_dir}

if [ $no_site_packages -eq 1 ]; then
    installvenvopts="--no-site-packages"
fi


if [ $never_venv -eq 0 ]
then
    # Remove the virtual environment if --force used
    if [ $force -eq 1 ]; then
        echo "Cleaning virtualenv..."
        rm -rf ${venv}
    fi
    if [ $update -eq 1 ]; then
        echo "Updating virtualenv..."
        virtualenv $installvenvopts $venv
    fi
    if [ -e ${venv} ]; then
        source $venv/bin/activate
    else
        if [ $always_venv -eq 1 ]; then
            # Automatically install the virtualenv
            virtualenv $installvenvopts $venv
            source $venv/bin/activate
        else
            echo -e "No virtual environment found...create one? (Y/n) \c"
            read use_ve
            if [ "x$use_ve" = "xY" -o "x$use_ve" = "x" -o "x$use_ve" = "xy" ]; then
                # Install the virtualenv and run the test suite in it
                virtualenv $installvenvopts $venv
                source $venv/bin/activate
            fi
        fi
    fi
fi

pip install -U -r requirements.txt
pip install -U -e .

RETURN=0
# echo -e "Flake8\n====================\n"
# flake8 hivemind

echo -e "\nTests\n====================\n"
nosetests -v
