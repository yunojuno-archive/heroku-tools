# -*- coding: utf-8 -*-
"""Package setup for heroku-tools CLI application."""
import os

from setuptools import setup, find_packages

dependencies = ['click', 'sarge', 'pyyaml', 'requests', 'dateutils']

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
# requirements.txt must be included in MANIFEST.in and include_package_data must be True
# in order for this to work; ensures that tox can use the setup to enforce requirements
REQUIREMENTS = '\n'.join(open(os.path.join(os.path.dirname(__file__), 'requirements.txt')).readlines())  # noqa

setup(
    name='heroku-tools',
    version='0.3.1',
    url='https://github.com/yunojuno/heroku-tools',
    license='MIT',
    author='Hugo Rodger-Brown',
    author_email='hugo@yunojuno.com',
    description=(
        "Command line application for managing Heroku applications."
    ),
    long_description=README,
    packages=find_packages(),
    include_package_data=True,
    install_requires=REQUIREMENTS,
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
