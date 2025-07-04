#!/usr/bin/env python
# -- coding: utf-8 --
"""
Copyright 2013, Big Switch Networks, Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

circuitpusher utilizes floodlight REST APIs to create a bidirectional circuit,
i.e., permanent flow entry, on all switches in route between two devices based
on IP addresses with specified priority.  Now extended to include SSH (TCP/22).

Notes:
 1. The circuit pusher currently only creates circuits with two IP endpoints.
 2. Before sending REST API requests, the endpoints must be known to the controller
    (i.e., have sent any packet; a simple ping suffices).
 3. Supported syntax:
    a) circuitpusher.py --controller={IP}:{port} --add --name {circuit-name}
    b) circuitpusher.py --controller={IP}:{port} --delete --name {circuit-name}

@author adapted
"""

import os
import sys
import json
import argparse
import time

# CLI arguments
parser = argparse.ArgumentParser(description='Circuit Pusher (with SSH support)')
parser.add_argument('--controller',
                    dest='controllerRestIp',
                    action='store',
                    default='localhost:8080',
                    help='controller IP:RESTport, e.g., localhost:8080')
parser.add_argument('--add',
                    dest='action',
                    action='store_const',
                    const='add',
                    default='add',
                    help='action: add or delete')
parser.add_argument('--delete',
                    dest='action',
                    action='store_const',
                    const='delete',
                    help='action: add or delete')
parser.add_argument('--type',
                    dest='type',
                    action='store',
                    default='ip',
                    help='valid types: ip')
parser.add_argument('--src',
                    dest='srcAddress',
                    action='store',
                    default='10.0.0.1',
                    help='source IP (A.B.C.D)')
parser.add_argument('--dst',
                    dest='dstAddress',
                    action='store',
                    default='10.0.0.3',
                    help='destination IP (A.B.C.D)')
parser.add_argument('--name',
                    dest='circuitName',
                    action='store',
                    default='h1_h3_circuit',
                    help='circuit name, e.g., h1_h3_circuit')

args = parser.parse_args()
ctrl = args.controllerRestIp

# Load existing circuits.json or init empty
if os.path.exists('./circuits.json'):
    with open('./circuits.json','r') as f:
        lines = f.readlines()
else:
    lines = []

if args.action == 'add':
    # avoid duplicates
    for l in lines:
        if json.loads(l)['name'] == args.circuitName:
            print(f"Circuit {args.circuitName} already exists.")
            sys.exit(1)
    cb = open('./circuits.json','a')

    # discover endpoints via Device Manager
    def discover(ip):
        out = os.popen(f"curl -s http://{ctrl}/wm/device/?ipv4={ip}").read()
        dev = json.loads(out)
        if not dev:
            print(f"ERROR: endpoint {ip} unknown; ping it first.")
            sys.exit(1)
        ap = dev[0]['attachmentPoint'][0]
        return ap['switchDPID'], ap['port']

    srcDPID, srcPort = discover(args.srcAddress)
    dstDPID, dstPort = discover(args.dstAddress)

    print(f"Creating circuit {args.circuitName}: {srcDPID}:{srcPort} ↔ {dstDPID}:{dstPort}")

    # fetch route
    route = json.loads(os.popen(
        f"curl -s http://{ctrl}/wm/topology/route/{srcDPID}/{srcPort}/{dstDPID}/{dstPort}/json"
    ).read())

    # for each hop pair, push IPv4, ARP, SSH flows
    for i in range(0, len(route), 2):
        sw1, p1 = route[i]['switch'], route[i]['port']
        sw2, p2 = route[i+1]['switch'], route[i+1]['port']

        # helper to send flow
        def push(flow):
            payload = json.dumps(flow)
            os.system(f"curl -s -d '{payload}' http://{ctrl}/wm/staticflowpusher/json")

        # Forward IPv4
        push({
            "switch": sw1,
            "name": f"{sw1}.{args.circuitName}.f",
            "ipv4_src": args.srcAddress,
            "ipv4_dst": args.dstAddress,
            "eth_type": "0x0800",
            "priority": "32768",
            "in_port": p1,
            "actions": f"output={p2}",
            "active": "true"
        })
        # Forward ARP
        push({
            "switch": sw1,
            "name": f"{sw1}.{args.circuitName}.farp",
            "arp_spa": args.srcAddress,
            "arp_tpa": args.dstAddress,
            "eth_type": "0x0806",
            "priority": "32768",
            "in_port": p1,
            "actions": f"output={p2}",
            "active": "true"
        })
        # Forward SSH (TCP/22)
        push({
            "switch": sw1,
            "name": f"{sw1}.{args.circuitName}.fssh",
            "ipv4_src": args.srcAddress,
            "ipv4_dst": args.dstAddress,
            "eth_type": "0x0800",
            "ip_proto": "6",
            "tcp_dst": "22",
            "priority": "32768",
            "in_port": p1,
            "actions": f"output={p2}",
            "active": "true"
        })

        # Reverse IPv4
        push({
            "switch": sw2,
            "name": f"{sw2}.{args.circuitName}.r",
            "ipv4_src": args.dstAddress,
            "ipv4_dst": args.srcAddress,
            "eth_type": "0x0800",
            "priority": "32768",
            "in_port": p2,
            "actions": f"output={p1}",
            "active": "true"
        })
        # Reverse ARP
        push({
            "switch": sw2,
            "name": f"{sw2}.{args.circuitName}.rarp",
            "arp_spa": args.dstAddress,
            "arp_tpa": args.srcAddress,
            "eth_type": "0x0806",
            "priority": "32768",
            "in_port": p2,
            "actions": f"output={p1}",
            "active": "true"
        })
        # Reverse SSH (TCP src 22)
        push({
            "switch": sw2,
            "name": f"{sw2}.{args.circuitName}.rssh",
            "ipv4_src": args.dstAddress,
            "ipv4_dst": args.srcAddress,
            "eth_type": "0x0800",
            "ip_proto": "6",
            "tcp_src": "22",
            "priority": "32768",
            "in_port": p2,
            "actions": f"output={p1}",
            "active": "true"
        })

        # record
        rec = {'name':args.circuitName, 'Dpid':sw1, 'inPort':p1, 'outPort':p2, 'time':time.asctime()}
        cb.write(json.dumps(rec)+"\n")

    cb.close()

elif args.action == 'delete':
    found = False
    new = []
    for l in lines:
        data = json.loads(l)
        if data['name'] == args.circuitName:
            sw = data['Dpid']
            for suf in ('.f','.farp','.fssh','.r','.rarp','.rssh'):
                nm = sw + '.' + args.circuitName + suf
                os.system(
                    f"curl -s -X DELETE -d '{{\"switch\":\"{sw}\",\"name\":\"{nm}\"}}' "
                    f"http://{ctrl}/wm/staticflowpusher/json"
                )
            found = True
        else:
            new.append(l)
    with open('./circuits.json','w') as cb:
        cb.writelines(new)
    if not found:
        print(f"Circuit {args.circuitName} not found.")
        sys.exit(1)
else:
    print(f"Unknown action {args.action}")
    sys.exit(1)
