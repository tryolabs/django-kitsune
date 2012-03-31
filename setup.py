'''
Created on Mar 31, 2012

@author: raul
'''

from setuptools import setup, find_packages

setup(name='django-kitsune',
      version=__import__('kitsune').get_version(limit=3),
      description='A Django Admin app to perform host server monitoring.',
      author='Raul Garreta - Tryolabs',
      author_email='raul@tryolabs.com',
      url='https://github.com/tryolabs/django-kitsune',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False
     )

