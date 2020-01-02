#!/usr/bin/python3
import sys
from dottod.dottod import Graph, clean_nmigen_graph, color_connections


ltp_data = open("/tmp/ltp").readlines()
for i, txt in enumerate(ltp_data):
    if txt.startswith("Longest topological path"):
        del ltp_data[:i+1]

for i in range(len(ltp_data)):
    line = ltp_data[i]
    colon =  line.find(':')
    ltp_data[i] = ltp_data[i][colon+3:].strip()
    space = ltp_data[i].find(" ")
    if space > 0:
        ltp_data[i] = ltp_data[i][:space]

    if ltp_data[i].startswith('\\'):
        ltp_data[i] = ltp_data[i][1:] #strip backslash
    ltp_data[i] = '"%s"'%ltp_data[i]


g = Graph()
g.read_dot(sys.argv[1])

for node in g.select_nodes(lambda n : n.label() in ltp_data):
    node.set_property("color", '"red"')
    node.set_property("fontcolor", '"red"')

clean_nmigen_graph(g)
color_connections(g)
g.write_dot("/tmp/ltp.dot")