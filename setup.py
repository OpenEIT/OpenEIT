from setuptools import setup, find_packages
import io
#import re
#import sys

# with io.open('./OpenEIT/__init__.py', encoding='utf8') as version_file:
#     version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file.read(), re.M)
#     if version_match:
#         version = version_match.group(1)
#     else:
#         raise RuntimeError("Unable to find version string.")


with io.open('README.md', encoding='utf8') as readme:
   long_description = readme.read()


NAME = 'eit_dash'
VERSION = '0.1.0'
AUTHOR = 'Jean Rintoul'
LICENSE = 'LICENSE'
INSTALL_REQUIRES = [
    'imageio==2.2.0',
    'matplotlib==2.1.1',
    'numpy==1.14.0',
    'pyserial==3.4',
    'scikit-image==0.13.1',
    'scipy==1.0.0',
    'six==1.11.0',
    'Adafruit-BluefruitLE==0.9.10',
    'dash==0.28.2',
    'dash-html-components==0.13.2',
    'dash_core_components==0.33.0',
    'PyObjC==5.0'
]


setup(
    name=NAME,
    version=VERSION,
    description='hello to the world',
    long_description=long_description,
    author=AUTHOR,
    author_email='jean@mindseyebiomedical.com',
    license=LICENSE,
    packages=find_packages(
        exclude=[
            'docs', 'tests',
            'windows', 'macOS', 'linux',
            'iOS', 'android',
            'django'
        ]
    ),
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: CC License',
    ],
    install_requires=INSTALL_REQUIRES, 

    # entry_points={
    #     'gui_scripts': [
    #         'Example = example.gui:main [GUI]',
    #     ],
    #     'console_scripts': [
    #         'utility = example.main:main',
    #     ]
    # },

    options={
        'app': {
            'formal_name': 'OpenEIT',
            'bundle': 'com.mindseyebiomedical'
        },
        # Desktop/laptop deployments
        'macos': {
            # 'app_requires': [
            #     'toga-cocoa==0.3.0.dev11',
            # ],
            'icon': 'icons/macos',
            #'splash': 'images/ios_splash',
        },
        # 'linux': {
        #     'app_requires': [
        #         'toga-gtk==0.3.0.dev11',
        #     ]
        # },
        # 'windows': {
        #     'app_requires': [
        #         'toga-winforms==0.3.0.dev11',
        #     ]
        # },

    }
)





# setup(
#     name=NAME,
#     version=VERSION,
#     author=AUTHOR,
#     license=LICENSE,
#     packages=find_packages(),
#     install_requires=INSTALL_REQUIRES,
# )
