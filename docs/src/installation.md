# Installation

There are multiple ways to install the charachorder.py library. Choose any one of the methods below that best suit your needs.

## From PyPI

You can use [pip](https://pip.pypa.io/en/stable) to install the package from PyPI

```sh
# Linux/macOS
python3 -m pip install -U charachorder.py

# Windows
py -3 -m pip install -U charachorder.py
```

## From source

You can build from source by cloning the repository and installing it using pip:

```sh
git clone https://github.com/GetPsyched/charachorder.py
cd charachorder.py
python3 -m pip install -U .
```

## Using nix shell

Running `nix shell github:GetPsyched/charachorder.py` will spawn a shell with Python 3.11 and this package installed. This has the caveat of not being able to change the Python version being used. To solve for this, use the package derivation itself (given below).

## Using shell.nix or flake.nix

Simply copy this derivation into your project and call it using `python3Packages.callPackage ./charachorder.nix { }`. If you don't know where to paste this, then this installation method is probably not for you.

```nix
{ buildPythonPackage, fetchFromGitHub, lib, pythonOlder, pyserial }:

buildPythonPackage rec {
  pname = "charachorder.py";
  version = "0.2.3";
  format = "setuptools";

  disabled = pythonOlder "3.8";

  src = fetchFromGitHub {
    owner = "GetPsyched";
    repo = pname;
    rev = "v${version}";
    hash = ""; # FIXME: Fill the hash here. Hint: Run this once and you will get the hash in the error
  };

  nativeBuildInputs = [ pyserial ];

  meta = with lib; {
    description = "A wrapper for CharaChorder's Serial API written in Python";
    downloadPage = "https://pypi.org/project/charachorder.py/#files";
    homepage = "https://github.com/GetPsyched/charachorder.py";
    license = licenses.mit;
    maintainers = [ maintainers.getpsyched ];
    platforms = platforms.all;
    sourceProvenance = [ sourceTypes.fromSource ];
  };
}
```
