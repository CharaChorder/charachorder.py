{
  buildPythonPackage,
  lib,
  pythonOlder,
  inquirer,
  pyserial,
}:

buildPythonPackage {
  pname = "charachorder.py";
  version = "0.6.0";
  format = "setuptools";

  disabled = pythonOlder "3.9";

  src = ./.;

  nativeBuildInputs = [
    inquirer
    pyserial
  ];

  meta = {
    description = "A wrapper for CharaChorder's Serial API written in Python";
    downloadPage = "https://pypi.org/project/charachorder.py/#files";
    homepage = "https://github.com/CharaChorder/charachorder.py";
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [ getpsyched ];
  };
}
