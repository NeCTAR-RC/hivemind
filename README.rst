Hivemind
========

Hivemind is a collection of Fabric commands used members of the NeCTAR
eResearch compute cloud.

Install on Ubuntu 14.04.2 LTS
-------

You need the following packages ::

  sudo apt-get install python-dev libxml2-dev libxslt-dev lib32z1-dev

You probably want a source install so run ::

  git clone git@github.com:NeCTAR-RC/hivemind.git
  cd hivemind
  sudo pip install -e .

Once that's done you will need to install https://github.com/NeCTAR-RC/hivemind_contrib
