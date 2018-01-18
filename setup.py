from setuptools import setup, find_packages

NAME = 'OpenEIT_Dashboard'
VERSION = '0.1.0'
AUTHOR = 'Jean Rintoul'
LICENSE = 'LICENSE'
INSTALL_REQUIRES = [
                    'cycler==0.10.0',
                    'decorator==4.2.1',
                    'imageio==2.2.0',
                    'matplotlib==2.1.1',
                    'networkx==2.0',
                    'numpy==1.14.0',
                    'Pillow==5.0.0',
                    'pyparsing==2.2.0',
                    'pyserial==3.4',
                    'python-dateutil==2.6.1',
                    'pytz==2017.3',
                    'PyWavelets==0.5.2',
                    'scikit-image==0.13.1',
                    'scipy==1.0.0',
                    'six==1.11.0',
                    
                ]

setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    license=LICENSE,
    packages = find_packages(),
    install_requires=INSTALL_REQUIRES,
)
