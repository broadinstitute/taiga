FROM ubuntu:latest

RUN apt-get update -y

# Preparing for yarn install
RUN apt-get install -y curl apt-transport-https
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list

# Install Nodejs/npm
RUN apt-get install -y nodejs npm

# Install python and its related packages
RUN apt-get install -y python3.5 python3-dev python3-pip python3-setuptools

RUN apt-get update -y

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
COPY taiga.tar.gz .
RUN tar -xzf taiga.tar.gz
RUN rm taiga.tar.gz

WORKDIR /taiga
#RUN python3.5 setup.py installl
RUN pip3 install -r requirements.txt

# Install backend javascript dependencies
RUN yarn install

# Install frontend javascript dependencies
WORKDIR frontend
RUN yarn install

WORKDIR ..
RUN python3.5 taiga2/create_test_db_sqlalchemy.py settings.cfg

# Build our frontend distribution
RUN ln -s /usr/bin/nodejs /usr/bin/node
RUN node_modules/.bin/webpack

# Set celery as being able to run as root => Can find a better way
ENV C_FORCE_ROOT=true
# Set where celery can find the settings
ENV TAIGA2_SETTINGS="settings.cfg"

# Install supervisor
RUN mkdir -p /var/log/supervisor
RUN mkdir -p /var/run
RUN apt-get install -y supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8080

CMD ["/usr/bin/supervisord"]
#ENTRYPOINT ["supervisor"]
#CMD ["settings.cfg"]