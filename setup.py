#!/usr/bin/env python3

from pathlib import Path

from setuptools import find_packages, setup

packages = find_packages(exclude=("tests*",))
package_data = {pkg: ("py.typed", "requirements.txt") for pkg in packages}
scripts = tuple(map(str, Path("scripts").iterdir()))


setup(
    name="py_dev",
    python_requires=">=3.8.0",
    version="0.1.0",
    description="python dev tools",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    author="ms-jpq",
    author_email="github@bigly.dog",
    url="https://github.com/ms-jpq/py-dev",
    scripts=scripts,
    packages=packages,
    package_data=package_data,
)
