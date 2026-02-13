{ pkgs, lib, config, inputs, ... }:

let
  root = config.git.root;
in
{
  # https://devenv.sh/basics/
  env.GREET = "Confidantic";
  env.CONFIDANTIC_ROOT = "${root}/.devman/.config";

  # https://devenv.sh/packages/
  packages = with pkgs; [
    git
    just
    jq
    cue
    tree-sitter
  ];

  # https://devenv.sh/languages/
  # languages.rust.enable = true;
  languages = {
      python = {
          enable = true;
          version = "3.13";
          venv.enable = true;
          uv.enable = true;
        };
    };

  # https://devenv.sh/processes/
  # processes.cargo-watch.exec = "cargo-watch";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # # https://devenv.sh/scripts/
  # scripts.hello.exec = ''
  #   echo hello from $GREET
  # '';

  # Intentionally do not set CONFIDANTIC_PROFILE here.
  env.JUSTFILE = ".devman/justfile";

  scripts.confidantic.exec = ''
    exec uv run --project "${root}" confidantic "$@"
  '';

  scripts.confidantic-cue.exec = ''
    exec cue "$@"
  '';

  scripts.test.exec = "just test";

  scripts.confidantic-phase6.exec = ''
    exec uv run --project "${root}" python scripts/ci/phase6_quality_gates.py "$@"
  '';

  enterShell = ''
    echo
    echo --------------------------------------------------------
    echo
    echo " Welcome to the Devman development environment! "
    # echo
    # echo " To get started, try running: devman launch"
    echo
    echo --------------------------------------------------------
    echo
    git --version
    # echo
    # echo IWD: "$(pwd)"
    echo
    cd "${root}"
    echo PWD: "$(pwd)"
    mkdir -p "$CONFIDANTIC_ROOT"
    echo
  '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # # https://devenv.sh/tests/
  # enterTest = ''
  #   echo "Running tests"
  #   git --version | grep --color=auto "${pkgs.git.version}"
  # '';

  # https://devenv.sh/pre-commit-hooks/
  # pre-commit.hooks.shellcheck.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
