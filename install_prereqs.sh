set -ex
pip install -r requirements.txt
python setup.py develop
yarn install
cd react_frontend/ && yarn install && cd ..
