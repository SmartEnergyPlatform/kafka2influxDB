FROM python:3.6

RUN apt-get update \
    && apt-get install -y git \
    && git clone https://github.com/edenhill/librdkafka.git \
    && cd librdkafka \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && cd .. 
    #&& rm -rf librdkafka \
    #&& apt-get purge -y git \
    #&& apt-get clean -y \
    #&& apt-get autoclean -y \
    #&& apt-get autoremove -y \
    #&& rm -rf /var/cache/debconf/*-old \
    #&& rm -rf /var/lib/apt/lists/* \
    #&& rm -rf /usr/share/doc/* \
    #&& rm -rf /usr/local/manual/mod \
    #&& rm -rf /usr/local/manual/programs \
    #&& rm -rf /usr/share/vim/*/doc

ADD . /opt/kafka-influxdb
WORKDIR /opt/kafka-influxdb
RUN pip install --no-cache-dir -r requirements.txt
CMD [ "python", "./main.py" ]