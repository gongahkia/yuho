#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_VERSION="${YUHO_PYTHON:-3.13}"
VENV_DIR=".venv"
EXTRAS="dev"
USE_VENV=1
FORCE=0
RUN_SMOKE=1
INSTALL_UV=1

usage() {
    cat <<'EOF'
Usage: ./install.sh [OPTIONS]

Bootstrap Yuho from a local checkout.

Options:
  --python VERSION   Python version for uv venv (default: 3.13)
  --venv PATH        Virtualenv path (default: .venv)
  --no-venv          Install into the active Python environment
  --minimal          Install runtime deps only, without dev extras
  --dev              Install dev extras (default)
  --force            Recreate the venv if it already exists
  --no-smoke         Skip post-install smoke checks
  --no-install-uv    Do not install uv if missing
  -h, --help         Show this help
EOF
}

log() {
    printf '[yuho] %s\n' "$1"
}

die() {
    printf '[yuho] error: %s\n' "$1" >&2
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --python)
            PYTHON_VERSION="${2:?missing value for --python}"
            shift 2
            ;;
        --venv)
            VENV_DIR="${2:?missing value for --venv}"
            shift 2
            ;;
        --no-venv)
            USE_VENV=0
            shift
            ;;
        --minimal)
            EXTRAS=""
            shift
            ;;
        --dev)
            EXTRAS="dev"
            shift
            ;;
        --force)
            FORCE=1
            shift
            ;;
        --no-smoke)
            RUN_SMOKE=0
            shift
            ;;
        --no-install-uv)
            INSTALL_UV=0
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "unknown option: $1"
            ;;
    esac
done

cd "$ROOT"

if ! command -v uv >/dev/null 2>&1; then
    if [[ "$INSTALL_UV" -eq 0 ]]; then
        die "uv not found; install uv or rerun without --no-install-uv"
    fi
    log "installing uv"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if [[ "$USE_VENV" -eq 1 ]]; then
    if [[ -d "$VENV_DIR" && "$FORCE" -eq 1 ]]; then
        log "removing $VENV_DIR"
        rm -rf "$VENV_DIR"
    fi
    if [[ ! -d "$VENV_DIR" ]]; then
        log "creating $VENV_DIR with Python $PYTHON_VERSION"
        uv venv --python "$PYTHON_VERSION" "$VENV_DIR"
    else
        log "using existing $VENV_DIR"
    fi
    # shellcheck disable=SC1090
    source "$VENV_DIR/bin/activate"
    INSTALL=(uv pip install)
else
    INSTALL=(python -m pip install)
fi

if [[ -n "$EXTRAS" ]]; then
    TARGET=".[${EXTRAS}]"
else
    TARGET="."
fi

log "installing Yuho: ${INSTALL[*]} -e $TARGET"
"${INSTALL[@]}" -e "$TARGET"

if [[ "$RUN_SMOKE" -eq 1 ]]; then
    OUT_DIR="${TMPDIR:-/tmp}/yuho-smoke"
    mkdir -p "$OUT_DIR"
    log "smoke: version"
    yuho --version
    log "smoke: doctor"
    yuho doctor
    log "smoke: check s415"
    yuho check library/penal_code/s415_cheating/statute.yh
    log "smoke: transpile english"
    yuho transpile -t english library/penal_code/s415_cheating/statute.yh -o "$OUT_DIR/s415.txt"
    log "smoke: verify capabilities"
    yuho verify --capabilities
    log "smoke: starter workspace"
    yuho init "$OUT_DIR/starter" --force
fi

cat <<EOF

Yuho is installed.
Use:
EOF
if [[ "$USE_VENV" -eq 1 ]]; then
    printf '  source %s/bin/activate\n' "$VENV_DIR"
fi
cat <<'EOF'
  yuho init yuho-starter
  yuho doctor
  yuho check library/penal_code/s415_cheating/statute.yh
  yuho completion zsh --install
EOF
