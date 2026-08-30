#!/usr/bin/env bash
# Prepare photos for the website. macOS only (uses `sips`, which is built in).
#
#   ./tools/prep-images.sh art        <- process new files in assets/img/art/
#   ./tools/prep-images.sh badminton
#
# Drop any photo (JPEG, PNG, HEIC — straight from your phone is fine) into
# assets/img/<gallery>/ and run this. It resizes the original to 1800px for the
# click-through view and writes a 700px thumbnail into thumb/ for the grid.
# Files that already have a thumbnail are skipped.

set -euo pipefail
GALLERY="${1:-}"
[ -z "$GALLERY" ] && { echo "usage: $0 <art|badminton>"; exit 1; }

DIR="$(cd "$(dirname "$0")/.." && pwd)/assets/img/$GALLERY"
[ -d "$DIR" ] || { echo "no such gallery: $DIR"; exit 1; }
mkdir -p "$DIR/thumb"

shopt -s nullglob nocaseglob
for f in "$DIR"/*.{jpg,jpeg,png,heic}; do
  name="$(basename "${f%.*}").jpg"
  [ -f "$DIR/thumb/$name" ] && continue
  echo "processing $(basename "$f")"
  sips -s format jpeg -Z 1800 -s formatOptions 72 "$f" --out "$DIR/$name"       >/dev/null
  sips -s format jpeg -Z 700  -s formatOptions 68 "$f" --out "$DIR/thumb/$name" >/dev/null
  # remove the original if it was not already a .jpg of the same name
  [ "$f" != "$DIR/$name" ] && rm "$f"
done
echo "done. Run 'python3 build.py' to see it."
