# See full reference at https://devenv.sh/reference/options/
{ pkgs, lib, config, inputs, ... }:
let
  pkgs-unstable = import inputs.nixpkgs-unstable { system = pkgs.stdenv.system; };
  # Workaround for https://github.com/cachix/devenv/issues/1678
  pyright = (
    (pkgs.writeShellApplication {
      name = "pyright";
      runtimeInputs = [ pkgs.pyright ];
      text = ''
        cd ${
          lib.escapeShellArg (
            lib.strings.normalizePath config.devenv.root
          )
        }
        uv run pyright "$@"
      '';
    }).overrideAttrs
      (oldAttrs: {
        name = "pyright-in-venv";
      })
  );
in
{
  packages = [
    pkgs.nodejs
  ];

  languages.python.enable = true;
  languages.python.version = "3.13";
  languages.python.uv.enable = true;
  languages.python.uv.package = pkgs-unstable.uv;
  languages.python.uv.sync.enable = true;
  languages.python.uv.sync.arguments = ["--frozen"];
  languages.python.venv.enable = true;

  enterTest = ''
    pytest
  '';

  git-hooks.hooks.pyright.enable = true;
  git-hooks.hooks.pyright.package = pyright;
  git-hooks.hooks.pyright.args = ["--warnings"];
  git-hooks.hooks.ruff.enable = true;
  git-hooks.hooks.ruff-format.enable = true;

  dotenv.disableHint = true;
  env.LD_LIBRARY_PATH = lib.makeLibraryPath (with pkgs; [
    zlib
  ]);
}
