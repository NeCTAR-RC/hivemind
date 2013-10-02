#!/bin/bash

set -x

virtualenv .

source bin/activate

pip install -r requirements.txt
pip install -e .

RETURN=0

for file in $(find . -name \*.py)
do
    pyflakes $file
    if [ ! $? -eq 0 ]
    then
        RETURN=1
    fi
done

./bin/nosetests -v
if [ ! $? -eq 0 ]
then
    RETURN=1
fi

exit $RETURN
