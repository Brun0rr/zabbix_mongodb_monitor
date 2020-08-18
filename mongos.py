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

mongoshosts = os.environ['MONGOSHOSTS'].split(",")
mongoshardsvrhosts = os.environ['MONGOSHARDSVRHOSTS'].split(",")
mongoconfigsvrhosts = os.environ['MONGOCONFIGSVRHOSTS'].split(",")
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

def getPacket_mongos(mongohost):
    global insert
    global query
    global update
    global delete
    global getmore
    global command
    host_key = mongohost.split('.')[0]
    host_index = int(host_key.split('-')[-1])
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

def getPacket_rs(mongohost, item_key):
    host_key = mongohost.split('.')[0]
    res = run_command(mongohost, 'replSetGetStatus')
    packet = []
    packet.append(ZabbixMetric(zbhost, item_key + "[" + host_key + "]", int(res["myState"])))
    return packet

def sendLLD(url_hosts, item_key):
    print('Sending LLD to ' + item_key)
    json_lld = []
    for mongohost in url_hosts:
        json_lld.append({"host": mongohost.split('.')[0]})
    packet = [ ZabbixMetric(zbhost, item_key, json.dumps(json_lld)) ]
    t = ZabbixSender(zabbix_port = zbport, zabbix_server = zbserver).send(packet)
    print(t)
    
if len(mongoshosts) > 0:
    sendLLD(mongoshosts, 'mongos_lld')
if len(mongoshardsvrhosts) > 0:
    sendLLD(mongoshardsvrhosts, 'mongoshardsvr_lld')
if len(mongoconfigsvrhosts) > 0:
    sendLLD(mongoconfigsvrhosts, 'mongoconfigsvr_lld')

print("Initializing counters. It takes " + str(run_every) + " seconds")
for mongohost in mongoshosts:
    getPacket_mongos(mongohost)
time.sleep(run_every)

while True:
    for mongohost in mongoshosts:
        print("Running for " + mongohost.split('.')[0] + ": " + datetime.now().strftime("%H:%M:%S"))
        packet = getPacket_mongos(mongohost)

        # Send packet to Zabbix
        t = ZabbixSender(zabbix_port = zbport, zabbix_server = zbserver).send(packet)
        print(t)

    for mongoshardsvrhost in mongoshardsvrhosts:
        print("Running for " + mongoshardsvrhost.split('.')[0] + ": " + datetime.now().strftime("%H:%M:%S"))
        packet = getPacket_rs(mongoshardsvrhost, "mongos_rs_state")

        # Send packet to Zabbix
        t = ZabbixSender(zabbix_port = zbport, zabbix_server = zbserver).send(packet)
        print(t)
    
    for mongoconfigsvrhost in mongoconfigsvrhosts:
        print("Running for " + mongoconfigsvrhost.split('.')[0] + ": " + datetime.now().strftime("%H:%M:%S"))
        packet = getPacket_rs(mongoconfigsvrhost, "mongos_config_rs_state")
        
        # Send packet to Zabbix
        t = ZabbixSender(zabbix_port = zbport, zabbix_server = zbserver).send(packet)
        print(t)


    # Run every X Seconds
    time.sleep(run_every)