#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${ROOT_DIR}/asset/demo"
TMP_DIR="$(mktemp -d)"
FONT_ARGS=()

trap 'rm -rf "${TMP_DIR}"' EXIT

for tool in cabal rsvg-convert magick; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
        echo "missing required tool: ${tool}" >&2
        exit 1
    fi
done

mkdir -p "${ASSET_DIR}"

if [[ -f /System/Library/Fonts/Menlo.ttc ]]; then
    FONT_ARGS=(-font /System/Library/Fonts/Menlo.ttc)
elif [[ -f /System/Library/Fonts/Monaco.ttf ]]; then
    FONT_ARGS=(-font /System/Library/Fonts/Monaco.ttf)
fi

SVG_OUT="${ASSET_DIR}/brown-legal-diff.svg"
GIF_OUT="${ASSET_DIR}/brown-legal-diff.gif"
LEFT_EXAMPLE="examples/legal/brown_plaintiffs.euclid"
RIGHT_EXAMPLE="examples/legal/brown_board.euclid"

cd "${ROOT_DIR}"

cabal run exe:euclid -- diff "${LEFT_EXAMPLE}" "${RIGHT_EXAMPLE}" -f svg -o "${SVG_OUT}"

rsvg-convert -w 1200 -h 675 "${SVG_OUT}" -o "${TMP_DIR}/full.png"

caption_frame() {
    local input="$1"
    local caption="$2"
    local output="$3"

    magick "${input}" \
        -fill 'rgba(17,24,39,0.88)' -draw 'rectangle 0,608 1200,675' \
        "${FONT_ARGS[@]}" -fill '#f9fafb' -pointsize 24 -annotate +36+648 "${caption}" \
        "${output}"
}

caption_frame "${TMP_DIR}/full.png" \
    'euclid diff examples/legal/brown_plaintiffs.euclid examples/legal/brown_board.euclid' \
    "${TMP_DIR}/frame-1.png"

magick "${TMP_DIR}/full.png" \
    -fill none -stroke '#60a5fa' -strokewidth 6 -draw 'roundrectangle 22,62 570,650 12,12' \
    "${TMP_DIR}/left-highlight.png"
caption_frame "${TMP_DIR}/left-highlight.png" \
    'Plaintiffs narrative: equal protection and harm claims' \
    "${TMP_DIR}/frame-2.png"

magick "${TMP_DIR}/full.png" \
    -fill none -stroke '#34d399' -strokewidth 6 -draw 'roundrectangle 618,62 1166,650 12,12' \
    "${TMP_DIR}/right-highlight.png"
caption_frame "${TMP_DIR}/right-highlight.png" \
    'Board narrative: district-court posture and separate-but-equal claim' \
    "${TMP_DIR}/frame-3.png"

magick "${TMP_DIR}/full.png" \
    -fill none -stroke '#ef4444' -strokewidth 7 -draw 'roundrectangle 20,78 1180,214 14,14' \
    "${TMP_DIR}/contradiction-highlight.png"
caption_frame "${TMP_DIR}/contradiction-highlight.png" \
    'Red contradiction edges make competing factual narratives reviewable' \
    "${TMP_DIR}/frame-4.png"

magick \
    -delay 120 "${TMP_DIR}/frame-1.png" \
    -delay 110 "${TMP_DIR}/frame-2.png" \
    -delay 110 "${TMP_DIR}/frame-3.png" \
    -delay 150 "${TMP_DIR}/frame-4.png" \
    -loop 0 "${GIF_OUT}"

echo "${SVG_OUT}"
echo "${GIF_OUT}"
