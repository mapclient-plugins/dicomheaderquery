from setuptools import setup, find_packages
from mapclientplugins.dicomheaderquerystep import __version__ as version

dependencies = ['pydicom']

setup(name=u'mapclientplugins.dicomheaderquerystep',
      version=version,
      description='',
      long_description="",
      classifiers=[],
      author=u'Hugh Sorby',
      author_email='',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup',]),
      namespace_packages=['mapclientplugins'],
      include_package_data=True,
      zip_safe=False,
      install_requires=dependencies,
      )
