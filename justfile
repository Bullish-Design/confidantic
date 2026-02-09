set shell := ["zsh", "-eu", "-o", "pipefail", "-c"]

scripts_dir := ".devman/scripts"

test:
    @python {{scripts_dir}}/test_install.py


