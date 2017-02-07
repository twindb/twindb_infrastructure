#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pip.req import parse_requirements
from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [str(ir.req) for ir in
                parse_requirements('requirements.txt', session=False)]

test_requirements = [str(ir.req) for ir in
                     parse_requirements('requirements_dev.txt', session=False)]

setup(
    name='twindb-infrastructure',
    version='1.1.1',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
