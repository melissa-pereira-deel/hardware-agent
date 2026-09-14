#!/usr/bin/env bash
# Create a new hardware knowledge wiki as a private git repo.
#
#   ./harness/kb/bootstrap.sh ~/dev/wiki-hardware
#
# Creates the three-tier structure, seeds INDEX.md and an example entry,
# installs a pre-commit lint gate, and makes the first commit THROUGH that
# gate - so the seeded entry is linted like every entry after it.

set -euo pipefail

TARGET="${1:?usage: bootstrap.sh <path>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LINT="$HERE/harness/kb/lint.py"

if [ -e "$TARGET" ]; then
  echo "refusing to overwrite existing path: $TARGET" >&2
  exit 1
fi

if [ ! -f "$LINT" ]; then
  echo "cannot find the linter at $LINT" >&2
  exit 1
fi

mkdir -p "$TARGET"/{raw,scratch,wiki/hardware,wiki/parts}
cp -R "$HERE/wiki-template/." "$TARGET/"
touch "$TARGET/wiki/parts/.gitkeep"

# raw/ holds cached third-party PDFs and is deliberately NOT tracked. The
# MANIFEST is, so a fresh clone can still say what was fetched and verify a
# re-fetch against the recorded hash.
if [ ! -f "$TARGET/raw/MANIFEST.tsv" ]; then
  printf 'filename\turl\tpublisher\tsha256\tretrieved\n' > "$TARGET/raw/MANIFEST.tsv"
fi

cd "$TARGET"
git init -q -b main

# Gate first, commit second. Installing the hook after the initial commit -
# as this script used to - meant the seeded entry, the template every later
# entry imitates, entered the wiki having never been linted.
mkdir -p .git/hooks
cat > .git/hooks/pre-commit <<HOOK
#!/usr/bin/env bash
# Installed by hardware-agent bootstrap.sh.
#
# The linter path below is absolute and baked in at bootstrap time. A relative
# path here was the original defect: it resolved to a directory that did not
# exist, and the failure blamed your entries rather than the install.
set -euo pipefail

LINT="$LINT"
ROOT="\$(git rev-parse --show-toplevel)"

# A gate that cannot run must fail loudly. Treating "couldn't check" as
# "checked and fine" is how a guardrail disappears without anyone noticing.
if ! command -v python3 >/dev/null 2>&1; then
  echo "wiki pre-commit: python3 not found, so the lint gate cannot run." >&2
  echo "  Install python3, or use --no-verify if you are bypassing on purpose." >&2
  exit 1
fi

if [ ! -f "\$LINT" ]; then
  echo "wiki pre-commit: linter missing at" >&2
  echo "    \$LINT" >&2
  echo "  This is an installation problem, not a problem with your entries." >&2
  echo "  Re-run bootstrap.sh, or fix the path in .git/hooks/pre-commit." >&2
  exit 1
fi

if ! python3 "\$LINT" "\$ROOT/wiki"; then
  echo "" >&2
  echo "Wiki lint failed. Fix the entries listed above, or commit with" >&2
  echo "--no-verify if you are deliberately staging work in progress." >&2
  exit 1
fi
HOOK
chmod +x .git/hooks/pre-commit

git add -A
git commit -qm "Bootstrap hardware knowledge wiki"

echo "Created $TARGET"
echo "  lint gate: .git/hooks/pre-commit -> $LINT"
echo "  the seeded entry passed that gate on this commit"
echo
echo "Next:"
echo "  1. Add a PRIVATE remote:  git remote add origin <private-repo-url>"
echo "  2. Point your agent at it and start with one real document."
