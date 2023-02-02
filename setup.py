from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in geolife_customapp/__init__.py
from geolife_customapp import __version__ as version

setup(
	name="geolife_customapp",
	version=version,
	description="Geolife CustomApp",
	author="Erevive",
	author_email="laxmantandon@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
