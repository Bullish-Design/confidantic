# Confidantic devenv module
#
# When imported, provides:
# - CONFIDANTIC_ROOT=<repo_root>/.devman/.config (always)
# - CONFIDANTIC_JUSTFILE pointing to the include-able justfile
# - Shell hook to mkdir -p "$CONFIDANTIC_ROOT"
# - Required packages on PATH: cue, jq, confidantic CLI, confidantic-cue
#
# Does NOT set CONFIDANTIC_PROFILE.
{ pkgs, lib, config, ... }:

let
  cfg = config.confidantic;
in
{
  options.confidantic = {
    enable = lib.mkEnableOption "Confidantic configuration management";

    root = lib.mkOption {
      type = lib.types.str;
      default = "${toString config.devenv.root}/.devman/.config";
      description = "CONFIDANTIC_ROOT directory path.";
    };

    package = lib.mkOption {
      type = lib.types.package;
      default = pkgs.python3Packages.buildPythonPackage {
        pname = "confidantic";
        version = "1.0.0a1";
        src = ../..;
        format = "pyproject";
        nativeBuildInputs = [ pkgs.python3Packages.hatchling ];
        propagatedBuildInputs = with pkgs.python3Packages; [
          pydantic
          typer
          rich
        ];
      };
      description = "The confidantic Python package.";
    };

    justfile = lib.mkOption {
      type = lib.types.str;
      default = "${toString ./.}/just/confidantic.just";
      description = "Path to the Confidantic justfile include.";
    };
  };

  config = lib.mkIf cfg.enable {
    # Environment variables
    env = {
      CONFIDANTIC_ROOT = cfg.root;
      CONFIDANTIC_JUSTFILE = cfg.justfile;
    };

    # Required packages
    packages = [
      pkgs.cue
      pkgs.jq
      cfg.package
    ];

    # Shell hook: ensure config root exists
    enterShell = ''
      mkdir -p "$CONFIDANTIC_ROOT"
      if [ -z "$(ls -A "$CONFIDANTIC_ROOT" 2>/dev/null)" ]; then
        echo "confidantic: config root is empty — run 'just config:validate' to initialize"
      fi
    '';
  };
}
