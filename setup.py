from setuptools import setup
import re

with open("charachorder/__init__.py") as f:
    match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE)
    if not match:
        raise RuntimeError("version is not set")
    version = match.group(1)

readme = ""
with open("readme.md") as f:
    readme = f.read()

packages = ["charachorder"]

setup(
    name="charachorder",
    author="GetPsyched",
    url="https://github.com/GetPsyched/charachorder.py",
    project_urls={
        "Issue tracker": "https://github.com/GetPsyched/charachorder.py/issues",
    },
    version=version,
    packages=packages,
    license="MIT",
    description="A wrapper for CharaChorder's Serial API written in Python",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=["pyserial"],
    python_requires=">=3.8.0",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
