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
          "requests",
          "lxml",
          "cssselect",
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
