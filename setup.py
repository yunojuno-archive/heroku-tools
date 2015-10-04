# -*- coding: utf-8 -*-
"""Package setup for heroku-tools CLI application."""
import os

from setuptools import setup

dependencies = ['click', 'sarge', 'pyyaml', 'requests', 'dateutils']

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

setup(
    name='heroku-tools',
    version='0.1.3',
    url='https://github.com/yunojuno/heroku-tools',
    license='MIT',
    author='Hugo Rodger-Brown',
    author_email='hugo@yunojuno.com',
    description=(
        "Command line application for managing Heroku applications."
    ),
    long_description=README,
    include_package_data=True,
    packages=[
        'heroku_tools',
    ],
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'heroku-tools = heroku_tools:entry_point',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
    ]
)
