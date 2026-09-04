#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIRED_UV_VERSION="0.11.14"
PYTHON_VERSION="${YUHO_PYTHON:-3.13}"
VENV_DIR=".venv"
EXTRAS="dev"
USE_VENV=1
FORCE=0
RUN_SMOKE=1

usage() {
    cat <<'EOF'
Usage: ./install.sh [OPTIONS]

Synchronize a Yuho checkout from its committed uv.lock.

Prerequisite: uv 0.11.14 must already be installed. This script deliberately
does not download a mutable installer or resolve new dependencies.

Options:
  --python VERSION   Python interpreter for uv (default: 3.13)
  --venv PATH        Project virtualenv path (default: .venv)
  --no-venv          Synchronize the active virtualenv instead
  --minimal          Install runtime dependencies only
  --dev              Install the locked dev extra (default)
  --force            Recreate the selected project virtualenv
  --no-smoke         Skip post-install smoke checks
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

command -v uv >/dev/null 2>&1 || die "uv ${REQUIRED_UV_VERSION} is required; install that exact version and retry"
UV_VERSION="$(uv --version | awk '{print $2}')"
[[ "$UV_VERSION" == "$REQUIRED_UV_VERSION" ]] || die "requires uv ${REQUIRED_UV_VERSION}; found ${UV_VERSION}"
uv lock --check

SYNC=(uv sync --locked --python "$PYTHON_VERSION")
RUN=(uv run --locked)

if [[ "$USE_VENV" -eq 1 ]]; then
    ROOT_REAL="$(realpath -m "$ROOT")"
    VENV_REAL="$(realpath -m "$VENV_DIR")"
    [[ "$VENV_REAL" != "/" && "$VENV_REAL" != "$ROOT_REAL" ]] || die "refusing unsafe virtualenv path: $VENV_DIR"

    if [[ -d "$VENV_REAL" && "$FORCE" -eq 1 ]]; then
        log "recreating $VENV_REAL"
        rm -rf -- "$VENV_REAL"
    fi

    export UV_PROJECT_ENVIRONMENT="$VENV_REAL"
else
    [[ -n "${VIRTUAL_ENV:-}" ]] || die "--no-venv requires an active virtualenv"
    SYNC+=(--active)
    RUN+=(--active)
fi

if [[ -n "$EXTRAS" ]]; then
    SYNC+=(--extra "$EXTRAS")
fi

log "synchronizing committed dependencies"
"${SYNC[@]}"

if [[ "$RUN_SMOKE" -eq 1 ]]; then
    OUT_DIR="${TMPDIR:-/tmp}/yuho-smoke"
    mkdir -p "$OUT_DIR"
    log "smoke: version"
    "${RUN[@]}" yuho --version
    log "smoke: doctor"
    "${RUN[@]}" yuho doctor
    log "smoke: check s415"
    "${RUN[@]}" yuho check library/penal_code/s415_cheating/statute.yh
    log "smoke: transpile english"
    "${RUN[@]}" yuho transpile -t english library/penal_code/s415_cheating/statute.yh -o "$OUT_DIR/s415.txt"
    log "smoke: verify capabilities"
    "${RUN[@]}" yuho verify --capabilities
    log "smoke: starter workspace"
    "${RUN[@]}" yuho init "$OUT_DIR/starter" --force
fi

cat <<EOF

Yuho is synchronized from uv.lock.
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
