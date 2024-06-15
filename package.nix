{ buildPythonPackage, lib, pythonOlder, inquirer, pyserial }:

buildPythonPackage rec {
  pname = "charachorder.py";
  version = "0.4.3";
  format = "setuptools";

  disabled = pythonOlder "3.9";

  src = ./.;

  nativeBuildInputs = [ inquirer pyserial ];

  meta = with lib; {
    description = "A wrapper for CharaChorder's Serial API written in Python";
    downloadPage = "https://pypi.org/project/charachorder.py/#files";
    homepage = "https://github.com/GetPsyched/charachorder.py";
    license = licenses.mit;
    maintainers = [ maintainers.getpsyched ];
  };
}
