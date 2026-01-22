set -ex
pre-commit install
poetry install
yarn install --cwd react_frontend