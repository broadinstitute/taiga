FROM us.gcr.io/cds-docker-containers/taiga-base:v1

COPY taiga2 /install/taiga/taiga2
COPY requirements.txt setup.py /install/taiga/
WORKDIR /install/taiga

RUN pip install -r requirements.txt

COPY react_frontend /install/taiga/react_frontend/
# Install frontend javascript dependencies
RUN cd /install/taiga/react_frontend && yarn install

RUN cd /install/taiga/react_frontend && ./node_modules/.bin/webpack

COPY flask setup_env.sh autoapp.py /install/taiga/
# Now we are using the right db, should use instead settings.cfg
#RUN python3.5 taiga2/create_test_db_sqlalchemy.py settings.cfg

# Build our frontend distribution
#RUN ln -s /usr/bin/nodejs /usr/bin/node
#RUN node_modules/.bin/webpack
#RUN export PATH="$(yarn global bin):$PATH"
#RUN yarn add webpack@2.2.1 --dev
# We build the production version TODO: Remove the exit 0
#RUN ./node_modules/.bin/webpack --config webpack.config.prod.js; exit 0

# Set celery as being able to run as root => Can find a better way
ENV C_FORCE_ROOT=true
# Set where celery can find the settings
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Configure supervisor
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8080

CMD ["/usr/bin/supervisord"]

