from sys import stdin
import requests
import pandas as pd
import json
import networkx as nx
from geographiclib.geodesic import Geodesic
import math
from datetime import datetime, timedelta


#Team member:Xinze Fan (xinzefan), Dezhou Chen (dezhouc2), Shraddha Sutar (ShraddhaSutar)



# time function
def time_min(t1,t2):
	"""Given two parameters t1 and t2 with datetime, return minutes in term of floor as float
	:param t1: first datetime
	:param t2: second datetime
	:return: minutes as float
	>>> time_min('5:43:50', '6:51:58')
	68
	>>> time_min('0:10:46', '0:54:54')
	44
	>>> time_min('10:48:35', '15:48:11')
	299
	"""
	t1 = t1[:8]
	t2 = t2[:8]
	t1 = datetime.strptime(t1, "%H:%M:%S")
	t2 = datetime.strptime(t2, "%H:%M:%S")
	time_delta = (t2 - t1)
	total_seconds = time_delta.total_seconds()
	minutes = total_seconds / 60
	return math.floor(minutes)



# distance function
def distance_cal (x1,y1,x2,y2):
	"""Given the two position with two coordinate for each position, return in miles as float
    :param x1: first position x1
    :param y1: first position y1
    :param x2: second position x2
    :param y2: second position y2
    :return: miles in float
    >>> distance_cal(12.68,20.57,28.91,35.24)
    1270.6604112910354
    >>> distance_cal(5.68, 7.95, 8.72, 20.81)
    788.006105005502
    >>> distance_cal(10.25, 14.11, 18.82, 51.49)
    2229.96418603418
    """
	geod = Geodesic.WGS84
	dist = geod.Inverse(float(x1),float(y1),float(x2),float(y2))
	return  dist['s12'] /1852.0



# given callsign, return the request from http
def datarequest(callsign):
	"""give the loaded data and returns the requested info from web and save as dic
    :param callsign: callsign information for flight
    :return: dictionary of dictionary
    >>> datarequest('aca738')
    {'callsign': 'ACA738', 'route': ['KSFO', 'CYYZ'], 'updateTime': 1593544124000, 'operatorIata': 'AC', 'flightNumber': 738}
    >>> datarequest('AAL2409')
    {'callsign': 'AAL2409', 'route': ['KMIA', 'KSTL'], 'updateTime': 1604888494000, 'operatorIata': 'AA', 'flightNumber': 2409}
    >>> datarequest('skw5296')
    {'callsign': 'SKW5296', 'route': ['KIND', 'KDEN'], 'updateTime': 1605307559000, 'operatorIata': 'OO', 'flightNumber': 5296}
	"""
	http = 'https://opensky-network.org/api/routes?callsign=' + str(callsign)
	test = requests.get(http)
	if test.text != '' and test.text.startswith('{"callsign"'):
		res = json.loads(test.text)
		return res
	else:
		return ''



# give the dic , add airport node to the graph
def addNode(G,result):
	"""add node in to G graph
	:param G: Given a graph
	:param result: given a flight information in dictionary
	:return: A Graph with node added
	>>> B = nx.DiGraph()
	>>> result ={"callsign":"FDX610","route":["KORD","KMEM"],"updateTime":1605367891000,"operatorIata":"FX","flightNumber":610}
	>>> N = addNode(B,result)
	>>> testn=nx.get_node_attributes(N,'Lattitude')
	>>> print(N.nodes())
	['KORD', 'KMEM']
	"""
	f = open('airport.txt', 'r')
	a = f.readlines()
	for nod in result['route']:
		if nod not in G.nodes():
			for line in a:
				l = line.split(',')
				icao = l[5].replace('"','')
				if icao == nod :
					latitude = l[6]
					longtitude = l[7]
					name = l[1]
					country = l[3]
					G.add_node(icao,Latitude = latitude, Longtitude = longtitude, Name = name, Country = country)
	return G



# add edge
def addEdge(G,result):
	"""add edges to the G graph
	:param G: given a Graph with nodes
	:return: A Graph with edges added to it
	>>> B = nx.DiGraph()
	>>> result ={"callsign":"FDX610","route":["KORD","KMEM"],"updateTime":1605367891000,"operatorIata":"FX","flightNumber":610}
	>>> N = addNode(B,result)
	>>> M = addEdge(N,result)
	>>> print(M.edges())
	[('KORD', 'KMEM')]
	"""
	x = nx.get_node_attributes(G, 'Latitude')
	y = nx.get_node_attributes(G, 'Longtitude')
	if len(result['route']) == 2:
		Start =result['route'][0]
		End = result['route'][1]
	# check start and end in the airport graph node and also get the coor for the distance
		x1 = x[Start]
		y1 = y[Start]
		x2 = x[End]
		y2 = y[End]
		distance = distance_cal(x1,y1,x2,y2)
		G.add_edge(Start,End,Distance = distance,Flight = result['callsign'])
	if len(result['route']) == 3 :
		Start = result['route'][0]
		Trans = result['route'][1]
		End = result['route'][2]
		x1 = x[Start]
		y1 = y[Start]
		x2 = x[Trans]
		y2 = y[Trans]
		x3 = x[End]
		y3 = y[End]
		distance1 = distance_cal(x1, y1, x2, y2)
		distance2 = distance_cal(x2, y2, x3, y3)
		G.add_edge(Start, Trans, Distance=distance1, Flight = result['callsign'])
		G.add_edge(Trans, End, Distance=distance2,Flight = result['callsign'])
	return G



if __name__ == "__main__":
	# read from steam
	data = stdin.readlines()
	# create empty graph
	G = nx.DiGraph()
	# set first time point
	t1 = data[1][30:38]
	# processing data
	for line in data:
		line = line.split(',')
		t2 = line[7]
		result = {}
		# within 5 min, read request and add node, edge to the graph
		if time_min(t1,t2) < 5:
			if line[10] != '' :
				result = datarequest(line[10])
				if result != '' :
					G = addNode(G,result)
					addEdge(G,result)
		# every 5 min, set new time point so that the later data keep processing as a new 5 min
		# and print out the request result.
		else:
			t1 = line[7]
			# How many distinct airports have been discovered?
			res1 = len(list(G.nodes()))
			print("There is "+ str(res1) + " distinct airports discovered now.")
			# list distinct country in graph
			cy = nx.get_node_attributes(G, 'Country')
			res2 = []
			for nod in G.nodes():
				re = cy[nod]
				if re not in res2:
					res2.append(re)
			print("List of distinct country: "+ str(res2))
			# percentage with have reverse edge
			p = nx.overall_reciprocity(G)
			print("The percentage with reverse edge: "+ str(p))
			# strongly connected
			sc = nx.is_strongly_connected(G)
			print("Is the graph a strongly connected: "+ str(sc))
			# weak connected
			wc = nx.is_weakly_connected(G)
			print("Is the graph a weakly_connected: "+ str(wc))
			# dead end
			deadend = []
			for nod1 in G.nodes():
				dec = False
				for nod2 in G.nodes():
					if G.has_edge(nod1, nod2):
						dec = True
				if dec == False:
					deadend.append(nod1)
			print("The dead end in the graph are : "+ str(deadend))