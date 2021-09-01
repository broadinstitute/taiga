FROM us.gcr.io/cds-docker-containers/taiga-base:v2

COPY taiga2 /install/taiga/taiga2
COPY requirements.txt setup.py /install/taiga/
WORKDIR /install/taiga

RUN pip install pip==21.1.2
RUN pip install -r requirements.txt

COPY react_frontend /install/taiga/react_frontend/
# Install frontend javascript dependencies
RUN cd /install/taiga/react_frontend && yarn install

RUN cd /install/taiga/react_frontend && ./node_modules/.bin/webpack

COPY flask setup_env.sh autoapp.py /install/taiga/

# Set celery as being able to run as root => Can find a better way
ENV C_FORCE_ROOT=true
# Set where celery can find the settings
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Configure supervisor
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8080

CMD ["/usr/bin/supervisord"]

