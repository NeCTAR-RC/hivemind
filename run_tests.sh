#!/bin/bash -e

virtualenv .

source bin/activate
pip install -r requirements.txt

RETURN=0

for file in $(find . -name \*.py)
do
    pyflakes $file
    if [ ! $? -eq 0 ]
    then
        RETURN=1
    fi
done

nosetests -v

exit $RETURN
