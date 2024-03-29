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
          "fabric<2.0.0",
          "prettytable==0.7.2",
          "requests",
          "lxml",
          "docutils",
          "cssselect",
          "python-debian==0.1.34",
          "chardet",   # from python-debian
          "cmd2",
      ],
      test_requires=[
          # -*- Extra requirements: -*-
          'mox',
          'mock',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      hivemind = hivemind.common:main_plus
      sixpack = hivemind.common:main

      [hivemind.packages]
      default = hivemind
      """,
      )
