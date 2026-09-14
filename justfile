# hardware-agent task runner.
#   just            list recipes
#   just setup      create the venv and install pinned deps
#   just test       run the harness test suite
#   just lint       lint the bundled wiki content and sanity-check the policy
#   just verify-broker   start the risk broker as a real MCP server and probe it

set shell := ["bash", "-uc"]

py := ".venv/bin/python"

default:
    @just --list

# Create .venv and install pinned dependencies. Uses uv when available.
setup:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v uv >/dev/null 2>&1; then
        echo "using uv"
        uv venv
        uv pip install -e ".[dev]"
    else
        echo "uv not found; falling back to venv + pip"
        python3 -m venv .venv
        .venv/bin/python -m pip install --upgrade pip
        .venv/bin/python -m pip install -e ".[dev]"
    fi
    echo
    echo "setup complete:"
    .venv/bin/python -c "import mcp, yaml, importlib.metadata as m; print('  mcp', m.version('mcp')); print('  pyyaml', yaml.__version__)"

# Run the harness test suite.
test:
    {{py}} -m pytest

# Lint the bundled wiki content and confirm the risk policy loads cleanly.
lint:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "== wiki content =="
    {{py}} harness/kb/lint.py wiki-template/wiki
    echo
    echo "== risk policy =="
    {{py}} -c "
    from risk_broker.tiers import Policy
    p = Policy()
    print(f'  {len(p.rules)} rules loaded, default_tier={p.default_tier}')
    assert p.default_tier == 3, 'default_tier must be 3 (fail closed)'
    print('  all patterns compiled, fails closed')
    "

# Start the broker as a real MCP server over stdio and exercise every tier.
verify-broker:
    {{py}} harness/verify_broker.py

# Check skill descriptions carry the vocabulary their trigger prompts use.
check-routing:
    {{py}} harness/check_skill_routing.py

# Show what the wiki write gate allows and blocks.
check-gate:
    {{py}} harness/kb/check_gate.py

# Create a new knowledge wiki at the given path.
bootstrap-wiki path:
    ./harness/kb/bootstrap.sh {{path}}

# Everything the definition of done requires.
check: test lint verify-broker check-routing
