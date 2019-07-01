set -ex
python setup.py develop
yarn install
cd frontend/ && yarn install && cd ..
