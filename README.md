# Configuration

1. Import template to Zabbix
2. Add This template to a host
3. Run the container `docker.io/o2boficial/zabbix_mongodb_monitor` with the environments bellow:
MONGOSHOSTS = List Mongos of IP/DNs, splited by ','
MONGOSHARDSVRHOSTS = List Mongo Config Servers of IP/DNs, splited by ','
MONGOCONFIGSVRHOSTS = List Mongo Shard Servers of IP/DNs, splited by ','
MONGO_PORT = Mongo Port
MONGO_USER = Mongo User
MONGO_PASS = Mongo PAss
ZABBIX_SERVER = Zabbix IP/DNS
ZABBIX_HOST = Zabbix Host Name
ZABBIX_PORT = Zabbix Port
RUN_EVERY_SECONDS = Run every X Seconds

