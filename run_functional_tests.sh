#!/usr/bin/env bash

# No 'set -euo pipefail'

if [ "$#" -ne 5 ]; then
    echo "❌ Usage: $0 <AWS_ACCESS_KEY_ID> <AWS_SECRET_ACCESS_KEY> <AWS_REGION> <PDFIX_SDK_NAME> <PDFIX_SDK_KEY>"
    exit 1
fi

export AWS_ACCESS_KEY_ID=$1
export AWS_SECRET_ACCESS_KEY=$2
export AWS_REGION=$3
export PDFIX_SDK_NAME=$4
export PDFIX_SDK_KEY=$5

VENV_DIR=".venv-functional-tests"

echo "🐍 Creating virtual environment..."
if ! python3 -m venv "$VENV_DIR"; then
    echo "❌ Failed to create virtual environment."
    exit 1
fi

echo "✅ Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "⬇️ Installing requirements..."
pip install --quiet --upgrade pip
pip install --quiet -r tests/functional/requirements_for_tests.txt

export PYTHONPATH="$(pwd)"

echo "🧪 Running functional tests with pytest..."
pytest -q tests/functional/
TEST_EXIT_CODE=$?

echo "🔻 Deactivating virtual environment..."
deactivate

echo "🧹 Cleaning up virtual environment and testing cache..."
rm -rf "$VENV_DIR"
rm -rf .pytest_cache

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All functional tests passed."
else
    echo "❌ Some functional tests failed."
    exit $TEST_EXIT_CODE
fi
