from setuptools import setup, find_packages
import os
import json

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from package.json
version = "0.0.1"
package_json = os.path.join(os.path.dirname(__file__), "package.json")
if os.path.exists(package_json):
	with open(package_json) as f:
		package_data = json.load(f)
		version = package_data.get("version", "0.0.1")

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