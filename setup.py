#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from os import path
import re
from setuptools import setup, find_packages


setup(
    name='gitlab-admin',
    version='0.1.0',
    author='Raphael Nestler',
    author_email='raphael.nestler@sensirion.com',
    description='Script to configure GitLab settings via REST API',
    license='BSD',
    keywords='gitlab',
    url='https://github.com/Sensirion/python-gitlab-admin',
    packages=['gitlab_admin'],
    long_description=open(path.join(path.dirname(__file__), 'README.rst')).read(),
    install_requires=open(path.join(path.dirname(__file__), 'requirements.txt')).readlines(),
    classifiers=[
        'Development Status :: Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
    ],
    entry_points={
        'console_scripts': [
            'gitlab-admin=gitlab_admin.gitlab_admin:main'
        ],
    }
)
