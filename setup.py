"""Setup module for Robot Framework Report Portal Listener package."""

# To use a consistent encoding
from codecs import open
from os import path

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='robotframework-reportportal-ng',
    version='1.0.0',
    description='A Robot Framework Report Portal Listener',
    long_description=long_description,
    url='https://github.com/ailjushkin/robotframework-reportportal',
    author='Alexander Iljushkin',
    author_email='ailjushkin@gmail.com',
    license='GPLv3',
    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',

        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.6',
    ],
    python_requires='~=2.7, ~=3.4, ~=3.6',
    keywords='testing,reporting,robot framework,reportportal',
    packages=find_packages(),
    install_requires=['reportportal-client>=3.0.0', 'robotframework>=3.0.2'],
)