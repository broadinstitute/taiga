set -ex
pip install -r dev-requirements.txt
python setup.py develop
pre-commit install
yarn install --cwd react_frontend