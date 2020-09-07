#! /bin/sh
set -e
find . -name '*.py' -exec pyupgrade --py36-plus {} +
python -m black tests pytest_markdown
python -m isort tests pytest_markdown
python -m black tests pytest_markdown --check --diff
python -m flake8 tests pytest_markdown
python -m pytest
