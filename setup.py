from setuptools import setup, find_packages

NAME = 'OpenEIT_Dashboard'
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
    author=AUTHOR,
    license=LICENSE,
    packages=find_packages(),
    install_requires=INSTALL_REQUIRES,
)
