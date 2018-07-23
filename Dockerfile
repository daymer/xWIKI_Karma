# Version: 3.1
# docker build -t karma:3.1 -f ‪C:\Projects\xWIKI_Karma\karma_dockerfile C:\Projects\xWIKI_Karma\
# docker build -t karma:3.1 -f /home/drozhd/xWiki_Karma/Dockerfile /home/drozhd/xWiki_Karma
FROM python:3.6.2
MAINTAINER Dmitry Rozhdestvenskiy <dremsama@gmail.com>
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils \
    && apt-get -y install locales \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen \
    && apt-get -y install apt-transport-https freetds-dev unixodbc-dev git \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/8/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get -y update && ACCEPT_EULA=Y apt-get install msodbcsql \
    && mkdir /xWIKI_Karma \
    && cd /xWIKI_Karma \
    && git clone https://github.com/daymer/xWIKI_Karma \
    && pip install --upgrade pip \
    && pip install -r /xWIKI_Karma/requirements.txt \
    && pip install mysql-connector-python --allow-external mysql-connector-python \
    && mkdir /var/log/karma \
    && mkdir /var/log/karma/WebServer \
    && mkdir /var/log/karma/CC \
    && chmod +x /xWIKI_Karma/launch_web_server.sh
ADD Configuration.py /xWIKI_Karma/
EXPOSE 8081
CMD ["/bin/bash", "/xWIKI_Karma/launch_web_server.sh"]