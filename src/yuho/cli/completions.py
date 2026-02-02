"""
Shell completion script generation for Yuho CLI.

Generates completion scripts for bash, zsh, and fish shells.
Uses Click's built-in completion support.
"""

from typing import Literal
import click

# Shell completion templates

BASH_COMPLETION_SCRIPT = '''
# Yuho bash completion script
# Add to ~/.bashrc or ~/.bash_completion:
#   source <(yuho --show-completion bash)
# Or save to /etc/bash_completion.d/yuho

_yuho_completion() {
    local IFS=$'\\n'
    COMPREPLY=( $(env COMP_WORDS="${COMP_WORDS[*]}" \\
                 COMP_CWORD=$COMP_CWORD \\
                 _YUHO_COMPLETE=bash_complete $1) )
    return 0
}

complete -o default -F _yuho_completion yuho
'''

ZSH_COMPLETION_SCRIPT = '''
#compdef yuho
# Yuho zsh completion script
# Add to ~/.zshrc:
#   source <(yuho --show-completion zsh)
# Or save to a file in $fpath (e.g., ~/.zsh/completions/_yuho)

_yuho() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[yuho] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _YUHO_COMPLETE=zsh_complete yuho)}")

    for key descr in ${(kv)response}; do
        if [[ "$descr" == "_" ]]; then
            completions+=("$key")
        else
            completions_with_descriptions+=("$key":"$descr")
        fi
    done

    if [[ -n $googlemock_completions_with_descriptions ]]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [[ -n $completions ]]; then
        compadd -U -V unsorted -a completions
    fi
}

compdef _yuho yuho
'''

FISH_COMPLETION_SCRIPT = '''
# Yuho fish completion script
# Add to ~/.config/fish/completions/yuho.fish
# Or source directly: yuho --show-completion fish | source

function _yuho_completion
    set -l response (env _YUHO_COMPLETE=fish_complete COMP_WORDS=(commandline -cp) COMP_CWORD=(commandline -t) yuho)

    for completion in $response
        set -l metadata (string split "," -- $completion)
        set -l comp $metadata[1]
        set -l desc ""
        if test (count $metadata) -ge 2
            set desc $metadata[2]
        end
        if test -z "$desc"
            echo -e "$comp"
        else
            echo -e "$comp\\t$desc"
        end
    end
end

complete -c yuho -f -a "(_yuho_completion)"
'''


ShellType = Literal["bash", "zsh", "fish"]


def get_completion_script(shell: ShellType) -> str:
    """
    Get the shell completion script for the specified shell.

    Args:
        shell: The shell type ("bash", "zsh", or "fish")

    Returns:
        The completion script as a string

    Raises:
        ValueError: If shell type is not supported
    """
    scripts = {
        "bash": BASH_COMPLETION_SCRIPT,
        "zsh": ZSH_COMPLETION_SCRIPT,
        "fish": FISH_COMPLETION_SCRIPT,
    }

    if shell not in scripts:
        raise ValueError(
            f"Unsupported shell: {shell}. Supported: {', '.join(scripts.keys())}"
        )

    return scripts[shell].strip()


def print_completion_script(shell: ShellType) -> None:
    """
    Print the completion script for the specified shell.

    Args:
        shell: The shell type
    """
    click.echo(get_completion_script(shell))


def get_install_instructions(shell: ShellType) -> str:
    """
    Get installation instructions for the completion script.

    Args:
        shell: The shell type

    Returns:
        Installation instructions as a string
    """
    instructions = {
        "bash": """
# Bash completion installation:
# Option 1: Add to ~/.bashrc
echo 'eval "$(yuho completion bash)"' >> ~/.bashrc

# Option 2: Save to bash_completion.d (requires sudo)
yuho completion bash | sudo tee /etc/bash_completion.d/yuho

# Then restart your shell or run:
source ~/.bashrc
""",
        "zsh": """
# Zsh completion installation:
# Option 1: Add to ~/.zshrc
echo 'eval "$(yuho completion zsh)"' >> ~/.zshrc

# Option 2: Save to fpath directory
mkdir -p ~/.zsh/completions
yuho completion zsh > ~/.zsh/completions/_yuho
# Then add to ~/.zshrc: fpath=(~/.zsh/completions $fpath)

# Then restart your shell or run:
source ~/.zshrc
""",
        "fish": """
# Fish completion installation:
# Option 1: Save to completions directory
yuho completion fish > ~/.config/fish/completions/yuho.fish

# Option 2: Add to config.fish
echo 'yuho completion fish | source' >> ~/.config/fish/config.fish

# Completions will be available immediately in new shells
""",
    }

    if shell not in instructions:
        return f"No installation instructions for shell: {shell}"

    return instructions[shell].strip()
