#!/usr/bin/python3
#
import sys, getopt, os
from pyzabbix import ZabbixMetric, ZabbixSender
from pymongo import MongoClient
import time
import urllib
from datetime import datetime

insert = 0
query = 0
update = 0
delete = 0
getmore = 0
command = 0

mongohost = os.environ['MONGO_SERVER']
mongoport = os.environ['MONGO_PORT']
muser = os.environ['MONGO_USER']
mpass = os.environ['MONGO_PASS']
zbserver = os.environ['ZABBIX_SERVER']
zbhost = os.environ['ZABBIX_HOST']
zbport = int(os.environ['ZABBIX_PORT'])
run_every = int(os.environ['RUN_EVERY_SECONDS'])

# Get serverStatus stats
def get_server_status():
    try:
        mo = MongoClient('mongodb://' + muser + ':' + urllib.parse.quote(mpass) + '@' + mongohost + ':' + mongoport + '/admin', connectTimeoutMS=5000)
    except Exception as e:
        print ('Can\'t connect to '+mongohost) 
        print ("ERROR:", e)
        sys.exit(1)
    res = mo.admin.command('serverStatus')
    return res

def getPacket():
    global insert
    global query
    global update
    global delete
    global getmore
    global command
    res = get_server_status()
    packet = []
    packet.append(ZabbixMetric(zbhost, "mongos_connections_current", int(res["connections"]["current"])))
    packet.append(ZabbixMetric(zbhost, "mongos_connections_available", int(res["connections"]["available"])))
    packet.append(ZabbixMetric(zbhost, "mongos_connections_totalCreated", int(res["connections"]["totalCreated"])))
    packet.append(ZabbixMetric(zbhost, "mongos_insert", int(res["opcounters"]["insert"]) - insert))
    packet.append(ZabbixMetric(zbhost, "mongos_query", int(res["opcounters"]["query"]) - query))
    packet.append(ZabbixMetric(zbhost, "mongos_update", int(res["opcounters"]["update"]) - update))
    packet.append(ZabbixMetric(zbhost, "mongos_delete", int(res["opcounters"]["delete"]) - delete))
    packet.append(ZabbixMetric(zbhost, "mongos_getmore", int(res["opcounters"]["getmore"]) - getmore))
    packet.append(ZabbixMetric(zbhost, "mongos_command", int(res["opcounters"]["command"]) - command))
    packet.append(ZabbixMetric(zbhost, "mongos_ok", int(res["ok"])))
    # Updating counters
    insert = int(res["opcounters"]["insert"])
    query = int(res["opcounters"]["query"])
    update = int(res["opcounters"]["update"])
    delete = int(res["opcounters"]["delete"])
    getmore = int(res["opcounters"]["getmore"])
    command = int(res["opcounters"]["command"])
    return packet

print("Initializing counters. It takes " + str(run_every) + " seconds")
getPacket()
time.sleep(run_every)

while True:
    print("Running: " + datetime.now().strftime("%H:%M:%S"))
    packet = getPacket()

    # Send packet to Zabbix
    t = ZabbixSender(zabbix_port = zbport, zabbix_server = zbserver).send(packet)
    print(t)

    # Run every X Seconds
    time.sleep(run_every)