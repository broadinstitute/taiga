FROM ubuntu:latest

RUN apt-get update -y

# Preparing for yarn install
RUN apt-get install -y curl apt-transport-https
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list

# Install Nodejs/npm
RUN apt-get install -y build-essential
RUN curl -sL https://deb.nodesource.com/setup_6.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get install -y nodejs

RUN rm nodesource_setup.sh
# The command below was taking an old 4.X version of node, not supported by yarn
#RUN apt-get install -y nodejs npm

# Install vim
RUN apt-get install -y vim

# Install python and its related packages
RUN apt-get install -y python3.5 python3-dev python3-pip python3-setuptools

# Install postgresql minimal set binaries and headers
RUN apt-get install -y libpq-dev

# Pre-install the python packages needed by the app, so we don't have to reinstall them each time
# But still install new ones in case we need them
RUN pip3 install -q attrs==16.2.0 \
        connexion==1.0.129 \
        boto3==1.4.2 \
        Flask==0.11.1 \
        celery==4.0.0 \
        connexion==1.0.129 \
        redis==2.10.5 \
        requests==2.11.0 \
        six==1.10.0 \
        tinydb==3.2.1 \
        SQLAlchemy==1.1.4 \
        Flask-SQLAlchemy==2.1 \
        marshmallow-sqlalchemy==0.12.1 \
        flask-marshmallow==0.7.0 \
        marshmallow-enum==1.0 \
        marshmallow-oneofschema==1.0.3 \
        pytest==3.0.5 \
        freezegun==0.3.8 \
        python-magic==0.4.12 \
        h5py==2.6.0 \
        numpy==1.11.3 \
        psycopg2==2.6.2

# Install R dependencies
RUN gpg --keyserver keyserver.ubuntu.com --recv-key E084DAB9
RUN gpg -a --export E084DAB9 | apt-key add -
RUN echo "deb http://cran.rstudio.com/bin/linux/ubuntu xenial/" | tee -a /etc/apt/sources.list
RUN apt-get update -y
RUN apt-get -y install r-base r-base-dev
RUN echo "r <- getOption('repos'); r['CRAN'] <- 'http://cran.us.r-project.org'; options(repos = r);" > ~/.Rprofile
RUN Rscript -e "source(\"https://bioconductor.org/biocLite.R\"); biocLite(\"rhdf5\")"

RUN apt-get update -y

# Install supervisor
RUN mkdir -p /var/log/supervisor
RUN mkdir -p /var/run
RUN apt-get install -y supervisor

# Install redis
RUN apt-get install -y wget

WORKDIR redis
RUN wget http://download.redis.io/redis-stable.tar.gz
RUN tar xvzf redis-stable.tar.gz
WORKDIR redis-stable
RUN make
RUN cp src/redis-server /usr/bin/
RUN cp src/redis-cli /usr/bin/

WORKDIR ../../

# Install yarn
RUN apt-get install -y yarn

# Use the tar to get the source code of taiga
ADD taiga.tar.gz taiga/
WORKDIR /taiga

RUN pip3 install -r requirements.txt

# Install backend javascript dependencies
RUN yarn install

# Install frontend javascript dependencies
WORKDIR frontend
RUN yarn install

WORKDIR ..
# Now we are using the right db, should use instead settings.cfg
#RUN python3.5 taiga2/create_test_db_sqlalchemy.py settings.cfg

# Build our frontend distribution
#RUN ln -s /usr/bin/nodejs /usr/bin/node
#RUN node_modules/.bin/webpack
RUN export PATH="$(yarn global bin):$PATH"
RUN yarn add webpack --dev
# We build the production version
RUN ./node_modules/.bin/webpack --config webpack.config.prod.js; exit 0

# Set celery as being able to run as root => Can find a better way
ENV C_FORCE_ROOT=true
# Set where celery can find the settings
ENV TAIGA2_SETTINGS="settings.cfg"

# Configure supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8080

CMD ["/usr/bin/supervisord"]
#ENTRYPOINT ["supervisor"]
#CMD ["settings.cfg"]