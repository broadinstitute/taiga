set -ex
cd react_frontend
yarn install
./node_modules/.bin/webpack --mode=production
