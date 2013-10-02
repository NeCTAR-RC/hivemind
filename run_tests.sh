#!/bin/bash

virtualenv .

source bin/activate

pip install -r requirements.txt
pip install -e .

RETURN=0
echo -e "PyFlakes\n====================\n"
for file in $(find hivemind -name \*.py)
do
    pyflakes $file
    if [ ! $? -eq 0 ]
    then
        RETURN=1
    fi
done

echo -e "\nTests\n====================\n"
./bin/nosetests -v
if [ ! $? -eq 0 ]
then
    RETURN=1
fi

exit $RETURN
