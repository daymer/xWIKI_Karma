# Version: 3.0
# docker build -f ‪C:\Projects\xWIKI_Karma\karma_dockerfile C:\Projects\xWIKI_Karma\ -t karma:3.0
# docker build -f /home/drozhd/xWiki_Karma/Dockerfile /home/drozhd/xWiki_Karma -t karma:3.0
FROM python:3.6.2
MAINTAINER Dmitry Rozhdestvenskiy <dremsama@gmail.com>
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get -y install locales
# RUN dpkg-reconfigure locales
RUN locale-gen --purge en_US.UTF-8
RUN apt-get -y install apt-transport-https freetds-dev unixodbc-dev git
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/8/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get -y update
RUN ACCEPT_EULA=Y apt-get install msodbcsql
RUN mkdir /xWIKI_Karma
RUN cd /xWIKI_Karma
RUN git clone https://github.com/daymer/xWIKI_Karma
RUN pip install --upgrade pip
RUN pip install -r /xWIKI_Karma/requirements.txt
# CMD ["python", "/xWIKI_Karma/CustomModules/mysql-connector-python-2.1.7/setup.py install"] removed by "pip install mysql-connector-python"
RUN pip install mysql-connector-python --allow-external mysql-connector-python
RUN mkdir /var/log/karma
RUN mkdir /var/log/karma/WebServer
RUN mkdir /var/log/karma/CC
EXPOSE 8081
ADD Configuration.py /xWIKI_Karma/
RUN chmod +x /xWIKI_Karma/launch_web_server.sh
RUN /xWIKI_Karma/launch_web_server.sh