{
  description = "A wrapper for CharaChorder's Serial API written in Python";

  inputs = {
    flakey-devShells.url = "https://flakehub.com/f/GetPsyched/not-so-flakey-devshells/0.x.x.tar.gz";
    flakey-devShells.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs@{ nixpkgs, flakey-devShells, ... }:
    let
      systems = [ "i686-linux" "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      nixpkgsFor = function: forAllSystems (system: function nixpkgs.legacyPackages.${system});
    in
    {
      packages = nixpkgsFor (pkgs: {
        default = pkgs.python3.withPackages (py-pkgs: with py-pkgs; [
          (callPackage ./package.nix { })
        ] ++ (callPackage ./package.nix { }).nativeBuildInputs);
      });

      devShells = forAllSystems (system: {
        default =
          let
            flakey-devShell-pkgs = flakey-devShells.outputs.packages.${system};
            pkgs = nixpkgs.legacyPackages.${system};
          in
          with pkgs; mkShell {
            buildInputs = [
              mdbook
              (python39.withPackages (py-pkgs: with py-pkgs; [
                (inquirer.overrideAttrs {
                  patches = [ ./inquirer-symbol.patch ];
                })
                pyserial
                setuptools
              ]))

              (flakey-devShell-pkgs.default.override { environments = [ "nix" ]; })
              (flakey-devShell-pkgs.vscodium.override {
                environments = [ "nix" "python" ];
                extensions = with vscode-extensions; [
                  redhat.vscode-yaml
                  tamasfe.even-better-toml
                  yzhang.markdown-all-in-one
                ];
              })
            ];
          };
      });
    };
}
