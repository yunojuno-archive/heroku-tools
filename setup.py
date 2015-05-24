# -*- coding: utf-8 -*-
"""Package setup for heroku-tools CLI application."""
from setuptools import setup

dependencies = ['click', 'envoy', 'yaml', 'requests']

setup(
    name='heroku-tools',
    version='0.1.2',
    url='https://github.com/yunojuno/heroku-tools',
    license='MIT',
    author='Hugo Rodger-Brown',
    author_email='hugo@yunojuno.com',
    description=(
        "Opinionated command line application for managing deployment "
        "and configuration of Heroku applications."
    ),
    include_package_data=True,
    packages=[
        'heroku_tools',
    ],
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'deploy = heroku_tools.deploy:deploy',
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
