FROM python:3.7-slim
RUN pip3 install pymongo py-zabbix
WORKDIR /app
COPY mongos.py .
ENTRYPOINT ["/usr/local/bin/python3", "/app/mongos.py"]