from setuptools import setup, find_packages
from pip.download import PipSession
from pip.req import parse_requirements
import os

NAME = 'open_eit_sandbox'
AUTHOR = 'Marion Le Borgne'
VERSION = '0.0.1'
DESCRIPTION="Visualization & Analysis tools for OpenEIT."
REPO_DIR = os.path.dirname(os.path.realpath(__file__))

requirement_file = os.path.join(REPO_DIR, 'requirements.txt')
irs = parse_requirements(requirement_file, session=PipSession())
install_requires = [str(ir.req) for ir in irs]
setup(name=NAME,
      author=AUTHOR,
      version=VERSION,
      long_description=DESCRIPTION,
      package_dir={'': 'src'},
      packages=find_packages('src'),
      install_requires=install_requires,
      include_package_data=True)
