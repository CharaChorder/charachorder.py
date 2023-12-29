import re
from pathlib import Path

from setuptools import setup

with open("charachorder/__init__.py") as f:
    match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE)
    if not match:
        raise RuntimeError("version is not set")
    version = match.group(1)

PROJECT_URL = "https://github.com/GetPsyched/charachorder.py"

setup(
    name="charachorder.py",
    version=version,
    license="MIT",
    description="A wrapper for CharaChorder's Serial API written in Python",
    long_description=Path("readme.md").read_text(),
    long_description_content_type="text/markdown",
    url=PROJECT_URL,
    author="GetPsyched",
    author_email="dev@getpsyched.dev",
    project_urls={
        "Documentation": "https://getpsyched.github.io/charachorder.py",
        "Issue tracker": f"{PROJECT_URL}/issues",
    },
    packages=["charachorder"],
    include_package_data=True,
    python_requires=">=3.8.0",
    install_requires=["pyserial"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
