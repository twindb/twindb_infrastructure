#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'boto3'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='twindb-infrastructure',
    version='0.1.3',
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
            'twindb_aws=twindb_infrastructure.twindb_aws:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
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
