from setuptools import setup

PACKAGE = 'TracCC'
VERSION = '0.1.1'

setup(
  name=PACKAGE,
  version=VERSION,
  packages=['traccc'],
  package_data={'traccc' : ['htdocs/*.css', 'htdocs/*.gif']},
  author = "Tammo van Lessen",
  description = "A plugin to integrate Cruise Control into Trac",
  url = "http://oss.werkbold.de/trac-cc",
  license ="GPL"
)
