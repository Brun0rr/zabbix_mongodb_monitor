#!/usr/bin/python3
#
import sys, getopt, os
from pyzabbix import ZabbixMetric, ZabbixSender
from pymongo import MongoClient
import time
import urllib
import json
from datetime import datetime

insert = [0,0,0]
query = [0,0,0]
update = [0,0,0]
delete = [0,0,0]
getmore = [0,0,0]
command = [0,0,0]

mongoshosts = os.environ['MONGO_SERVERS'].split(",")
mongoport = os.environ['MONGO_PORT']
muser = os.environ['MONGO_USER']
mpass = os.environ['MONGO_PASS']
zbserver = os.environ['ZABBIX_SERVER']
zbhost = os.environ['ZABBIX_HOST']
zbport = int(os.environ['ZABBIX_PORT'])
run_every = int(os.environ['RUN_EVERY_SECONDS'])

def run_command(mongohost, command):
    try:
        mo = MongoClient('mongodb://' + muser + ':' + urllib.parse.quote(mpass) + '@' + mongohost + ':' + mongoport + '/admin', connectTimeoutMS=5000)
    except Exception as e:
        print ('Can\'t connect to '+mongohost) 
        print ("ERROR:", e)
        sys.exit(1)
    res = mo.admin.command(command)
    return res

def getPacket(mongohost):
    global insert
    global query
    global update
    global delete
    global getmore
    global command
    host_key = mongohost.split('.')[0]
    host_index = int(host_key.split('-')[1])
    res = run_command(mongohost, 'serverStatus')
    packet = []
    packet.append(ZabbixMetric(zbhost, "mongos_connections_current[" + host_key + "]", int(res["connections"]["current"])))
    packet.append(ZabbixMetric(zbhost, "mongos_connections_available[" + host_key + "]", int(res["connections"]["available"])))
    packet.append(ZabbixMetric(zbhost, "mongos_connections_totalCreated[" + host_key + "]", int(res["connections"]["totalCreated"])))
    packet.append(ZabbixMetric(zbhost, "mongos_insert[" + host_key + "]", int(res["opcounters"]["insert"]) - insert[host_index]))
    packet.append(ZabbixMetric(zbhost, "mongos_query[" + host_key + "]", int(res["opcounters"]["query"]) - query[host_index]))
    packet.append(ZabbixMetric(zbhost, "mongos_update[" + host_key + "]", int(res["opcounters"]["update"]) - update[host_index]))
    packet.append(ZabbixMetric(zbhost, "mongos_delete[" + host_key + "]", int(res["opcounters"]["delete"]) - delete[host_index]))
    packet.append(ZabbixMetric(zbhost, "mongos_getmore[" + host_key + "]", int(res["opcounters"]["getmore"]) - getmore[host_index]))
    packet.append(ZabbixMetric(zbhost, "mongos_command[" + host_key + "]", int(res["opcounters"]["command"]) - command[host_index]))
    packet.append(ZabbixMetric(zbhost, "mongos_ok[" + host_key + "]", int(res["ok"])))
    # Updating counters
    insert[host_index] = int(res["opcounters"]["insert"])
    query[host_index] = int(res["opcounters"]["query"])
    update[host_index] = int(res["opcounters"]["update"])
    delete[host_index] = int(res["opcounters"]["delete"])
    getmore[host_index] = int(res["opcounters"]["getmore"])
    command[host_index] = int(res["opcounters"]["command"])
    return packet

def sendLLD(mongoshosts):
    print('Sending LLD')
    json_lld = []
    for mongohost in mongoshosts:
        json_lld.append({"mongos_host": mongohost.split('.')[0]})
    packet = [ ZabbixMetric(zbhost, "mongos_lld", json.dumps(json_lld)) ]
    t = ZabbixSender(zabbix_port = zbport, zabbix_server = zbserver).send(packet)
    print(t)
    
sendLLD(mongoshosts)
print("Initializing counters. It takes " + str(run_every) + " seconds")
for mongohost in mongoshosts:
    getPacket(mongohost)
time.sleep(run_every)

while True:
    for mongohost in mongoshosts:
        print("Running for " + mongohost.split('.')[0] + ": " + datetime.now().strftime("%H:%M:%S"))
        packet = getPacket(mongohost)

        # Send packet to Zabbix
        t = ZabbixSender(zabbix_port = zbport, zabbix_server = zbserver).send(packet)
        print(t)

    # Run every X Seconds
    time.sleep(run_every)