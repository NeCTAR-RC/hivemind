Hivemind
========

Hivemind is a collection of Fabric commands used members of the NeCTAR
eResearch compute cloud.  It can be used to do fancy things like:
 * list users in a project from keystone
 * Build debian packages


Hivemind runs in python and a complete Hivemind install comprises two interdependent components;
1) the hivemind framework itself
2) the hivemind_contrib

These two parts must be installed in the same python virtual environment

Install
-------

You need the following packages ::

  ```sudo apt-get install python-dev libxml2-dev libxslt1-dev lib32z1-dev python-virtualenv libmysqlclient-dev```

You probably want a source install so run ::

  ```cd ~
  mkdir hivemind_all
  cd hivemind_all
  virtualenv venv
  . venv/bin/activate```

  ```git clone https://github.com/NeCTAR-RC/hivemind.git
  cd hivemind
  pip install -e .
  cd ..```

  ```git clone https://github.com/NeCTAR-RC/hivemind_contrib.git
  cd hivemind_contrib
  pip install -e .
  cd ..```

Invocation
----------
You must activate the virtual environment in order for hivemind to work.

  ```$ . ~/hivemind_all/venv/bin/activate
  (venv)$ hivemind
  hivemind>```

And when you are done with it, you should deactivate it;

  ```hivemind> exit
  (venv)$ deactivate
  $```

Usage
-----

  ```hivemind> help```
