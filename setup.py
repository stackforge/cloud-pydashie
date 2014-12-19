#! /usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt')

reqs = [str(ir.req) for ir in install_reqs]


setup(
    name='Cloud-PyDashie',
    version='0.2',
    packages=['pydashie',],
    include_package_data=True,
    install_requires=reqs,
    entry_points={
      'console_scripts': ['pydashie = pydashie.main:run_sample_app']
    },
    license='MIT',
    long_description=open('README.rst').read(),
)
