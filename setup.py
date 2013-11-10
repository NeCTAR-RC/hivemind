from setuptools import setup, find_packages

version = '0.1'

setup(name='hivemind',
      version=version,
      description="Collection of fabric tools for NeCTAR.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Nectar',
      author_email='',
      url='',
      license='GPLv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          "fabric",
          "prettytable",
          "requests",
          "lxml",
          "cssselect",
      ],
      test_requires=[
          # -*- Extra requirements: -*-
          'mox',
          'mock',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      hivemind = hivemind.common:main

      [hivemind.tasks]
      gerrit = hivemind.gerrit
      libvirt = hivemind.libvirt
      nagios = hivemind.nagios
      pbuilder = hivemind.pbuilder
      puppet = hivemind.puppet
      reprepro = hivemind.reprepro
      swift = hivemind.swift
      """,
      )
