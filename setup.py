from setuptools import setup, find_packages
import os

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in raso_sync/__init__.py
version = "0.0.1"
init_file = os.path.join(os.path.dirname(__file__), "raso_sync", "__init__.py")
if os.path.exists(init_file):
	with open(init_file) as f:
		for line in f:
			if line.startswith("__version__"):
				version = line.split("=")[1].strip().strip("'\"")
				break

setup(
	name="raso_sync",
	version=version,
	description="RASO POS System Sync API for ERPNext",
	author="Martynas Miliauskas",
	author_email="martynas2200@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)