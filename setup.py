#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


def parse_requirements(path):
    """
    Parses requirements from a file given by path and return a list consumable by setuptools.

    :param path: Path to requirements file
    :type path: str
    :return: List of requirements.
    :rtype: list
    """
    with open(path) as fp:
        reqs = fp.read().strip().split('\n')

    return [x for x in reqs if x and not x.strip().startswith('#')]


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = parse_requirements('requirements.txt')

test_requirements = parse_requirements('requirements_dev.txt')

setup(
    name='twindb-infrastructure',
    version='1.1.6',
    description="TwinDB Infrastructure is a collection of everything"
                " to manage TwinDB infrastructure",
    long_description=readme + '\n\n' + history,
    author="TwinDB Development Team",
    author_email='dev@twindb.com',
    url='https://github.com/twindb/twindb_infrastructure',
    packages=find_packages(),
    package_dir={'twindb_infrastructure':
                 'twindb_infrastructure'},
    entry_points={
        'console_scripts': [
            'twindb-aws=twindb_infrastructure.twindb_aws:main',
            'twindb-chef=twindb_infrastructure.twindb_chef:main',
            'twindb-galera=twindb_infrastructure.twindb_galera:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='twindb_infrastructure',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
