""" setup for assumerole cli tool """

from setuptools import setup

setup(
    name='assumerole',
    version='0.1.0',
    description='Easily switch between AWS IAM roles',
    url='https://github.com/dsikes/assumerole',
    author='Dan Sikes',
    author_email='dan.sikes@pearson.com',
    packages=['assumerole'],
    install_requires=['boto3'],
    entry_points={ 
        'console_scripts': [
            'assumerole=assumerole.cli:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/dsikes/assumerole/issues',
        'Source': 'https://github.com/dsikes/assumerole/',
    },
)