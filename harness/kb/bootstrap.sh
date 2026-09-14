#!/usr/bin/env bash
# Create a new hardware knowledge wiki as a private git repo.
#
#   ./harness/kb/bootstrap.sh ~/wiki-hardware
#
# Creates the three-tier structure, seeds INDEX.md and an example entry,
# installs a pre-commit hook that runs the linter, and makes the first commit.

set -euo pipefail

TARGET="${1:?usage: bootstrap.sh <path>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ -e "$TARGET" ]; then
  echo "refusing to overwrite existing path: $TARGET" >&2
  exit 1
fi

mkdir -p "$TARGET"/{raw,scratch,wiki/hardware,wiki/parts}
cp -r "$HERE/wiki-template/." "$TARGET/"

cd "$TARGET"
git init -q
git add -A
git commit -qm "Bootstrap hardware knowledge wiki"

# Gate: the linter runs before every commit.
mkdir -p .git/hooks
cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
set -e
if command -v python3 >/dev/null; then
  python3 "$(git rev-parse --show-toplevel)/../hardware-agent/harness/kb/lint.py" \
    "$(git rev-parse --show-toplevel)/wiki" || {
      echo ""
      echo "Wiki lint failed. Fix the entries above, or commit with --no-verify"
      echo "if you are deliberately staging work in progress."
      exit 1
    }
fi
HOOK
chmod +x .git/hooks/pre-commit

echo "Created $TARGET"
echo
echo "Next:"
echo "  1. Add a PRIVATE remote:  git remote add origin <private-repo-url>"
echo "  2. Edit the lint path in .git/hooks/pre-commit if hardware-agent lives elsewhere."
echo "  3. Point your agent at it and start with one real document."
