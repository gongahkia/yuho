# syntax=docker/dockerfile:1
#
# Locked verification image for the Yuho toolchain and checked-in corpus.
# Grammar generation is intentionally not performed here: the release gate
# installs the pinned repository-local Node CLI with `npm ci` and verifies the
# generated artifacts before this image is published.

FROM ghcr.io/astral-sh/uv:0.11.14@sha256:1025398289b62de8269e70c45b91ffa37c373f38118d7da036fb8bb8efc85d97 AS uv

# python:3.12.14-slim-trixie manifest list, resolved 2026-09-04.
FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea AS base

ARG SOURCE_DATE_EPOCH=1704067200
COPY --from=uv /uv /usr/local/bin/uv

ENV PATH="/workspace/.venv/bin:${PATH}" \
    PYTHONHASHSEED=0 \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH} \
    UV_LINK_MODE=copy

# Record the exact apt and compiler inputs in the image. The release workflow
# publishes BuildKit provenance for the resulting image digest.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        libxml2-utils \
    && mkdir -p /usr/share/yuho \
    && {
        printf 'source_date_epoch=%s\n' "${SOURCE_DATE_EPOCH}"; \
        uv --version; \
        cc --version | head -n 1; \
        dpkg-query -W -f '${Package}=${Version}\n' build-essential ca-certificates libxml2-utils; \
    } > /usr/share/yuho/build-inputs.txt \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Resolve only the committed dependency graph before copying the source.
COPY pyproject.toml uv.lock README.md ./
RUN uv lock --check && uv sync --locked --all-extras --no-install-project

COPY src ./src
COPY library ./library
COPY scripts ./scripts
COPY tests ./tests
COPY docs ./docs
COPY Makefile ./

RUN uv sync --locked --all-extras \
    && yuho check library/penal_code/s415_cheating/statute.yh

CMD ["make", "verify-core"]
