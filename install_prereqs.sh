set -ex
pip install -r requirements.txt
python setup.py develop
pre-commit install
yarn install
cd react_frontend/ && yarn install && cd ..
