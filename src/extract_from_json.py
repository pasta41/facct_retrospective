import ijson
import json
import argparse
import networkx as nx
from networkx.algorithms.community.centrality import girvan_newman
import networkx.algorithms.community as nx_comm
import os
import community as community_louvain
import csv
import matplotlib.pyplot as plt
import numpy as np
import subprocess
import pandas as pd

#python extract_from_json.py ../dblp.v12.json /home/sameer/Projects/Political-leaning/clusters_0.csv
# python extract_from_json.py /home/sameer/Projects/Political-leaning/dblpv13.json /home/sameer/Projects/Political-leaning/cl_exp-1_temp louvain_dir /home/sameer/Projects/Political-leaning/idCompare.txt 
#python extract_from_json.py /home/sameer/Projects/Political-leaning/extracted_l1.json /home/sameer/Projects/Political-leaning/cl_exp-1 --skip_extraction
#python extract_from_json.py /home/sameer/Projects/Political-leaning/extracted_l1.json /home/sameer/Projects/Political-leaning/cl_exp-os-1 louvain_dir /home/sameer/Projects/Political-leaning/idCompare.txt /home/sameer/Projects/Political-leaning/OSLOM2/Graph/extracted_records_edgelist.dat_oslo_files/tp1 --skip_extraction

class GraphGenerator:
	"""
	A class encapsulating the generation of a citation network of a subset of the articles from the Aminer dataset

	Attributes
	----------
	node_levels : dictionary
		A mapping from article ID to node level, where node level is 0 for FAccT papers, 1 for papers directly cited by FAccT papers, and so on.
	node_records : dictionary
		An mapping from article ID to the corresponding entry in the Aminer dataset
	extracted : bool
		True if all relevant article entries (network nodes) have already been extracted and stored in a new json file. False otherwise.
	sourceFile : file object
		Refers to the json file of extracted relevant articles if extracted is True. Refers to the Aminer json file if extracted is False.
	
	Methods
	-------
	explore_nodeset()
		Populates node_levels. Called only if extracted is False.

	extract_records()
		Populates node_records and saves the same to a new json. Called only if extracted is False.

	generate_network()
		Generates the network from node_records.
	"""
	def __init__(self, sourceFilePath, extracted, nodeIdPath = None):
		self.node_levels = {}
		self.node_records = {}
		self.sourceFilePath = sourceFilePath
		self.sourceFile = open(sourceFilePath, 'r')
		self.extracted = extracted
		self.G = nx.DiGraph()

		if nodeIdPath is not None:
			self.nodeIdList = self.get_nodeId_list(nodeIdPath)

	def get_nodeId_list(self, nodeIdPath):
		nodeIdList = []
		with open(nodeIdPath, 'r') as f:
			for line in f:
				nodeIdList.append(line.strip('\n'))
		print(nodeIdList)
		return nodeIdList

	def explore_nodeset(self):
		i = 0
		for item in ijson.items(self.sourceFile, "item", use_float = True):
			i += 1
			if i % 1000000 == 0:
				print(i, " first pass")
			try:
				#if ("Fairness" in item["venue"]["raw"] or "fairness" in item["venue"]["raw"]) and ("Accountability" in item["venue"]["raw"] or "accountability" in item["venue"]["raw"]) and ("conference" in item["venue"]["raw"] or "Conference" in item["venue"]["raw"]):
				#print(item["id"])
				item_id = item["_id"] if type(item["_id"]) is not dict else item["_id"]["$oid"]
				if item_id in self.nodeIdList:
					print("matched")
					node = item_id
					self.node_levels[node] = 0
					if "references" in item:
						for reference in item["references"]:
							if reference not in self.node_levels:
								self.node_levels[reference] = 1
			except KeyError:
				pass
		self.sourceFile.seek(0)
		i = 0
		for item in ijson.items(self.sourceFile, "item", use_float = True):
			i += 1
			if i % 1000000 == 0:
				print(i, " second pass")
			try:
				item_id = item["_id"] if type(item["_id"]) is not dict else item["_id"]["$oid"]
				if item_id in self.node_levels and self.node_levels[item_id] == 1:
					node = item_id
					if "references" in item:
						for reference in item["references"]:
							if reference not in self.node_levels:
								self.node_levels[reference] = 2
			except KeyError:
				pass
		print (len(self.node_levels))
		print ("# of nodes at level 0: ", list(self.node_levels.values()).count(0))
		print ("# of nodes at level 1: ", list(self.node_levels.values()).count(1))
		print ("# of nodes at level 2: ", list(self.node_levels.values()).count(2))

	def extract_records(self):
		self.sourceFile.seek(0)
		i = 0
		for item in ijson.items(self.sourceFile, "item", use_float = True):
			i += 1
			if i % 1000000 == 0:
				print(i, "extraction first pass")
			try:
				item_id = item["_id"] if type(item["_id"]) is not dict else item["_id"]["$oid"]
				if item_id in self.node_levels:
					node = item_id
					self.node_records[node] = item
			except KeyError:
				pass
		extractedFile = os.path.join(os.path.dirname(self.sourceFilePath), "extracted_records_v13.json")
		with open(extractedFile, 'w') as f_write:		
			json.dump(self.node_records, f_write, indent = 0)

	def edge_list(self):
		edge_list = []
		edgelistFile = os.path.join(os.path.dirname(self.sourceFilePath), "extracted_records_edgelist_v13.dat")
		with open(edgelistFile, 'w') as f_write:	
			for node_id, node_record in self.node_records.items():
				if "references" in node_record:
					references = node_record["references"]
					for reference_id in references:
						if str(reference_id) in self.node_records:
							edge_list.append((node_id, reference_id))
							f_write.write("{node_id}\t{reference_id}\n".format(node_id = node_id, reference_id = reference_id))
		return edge_list

	def generate_network(self):
		if self.extracted == True:
			print("Loading from pre-extracted json")
			self.node_records = json.load(self.sourceFile)
			print("Number of records found in the json: ", len(self.node_records))
		else:
			self.explore_nodeset()
			self.extract_records()

		edge_list = self.edge_list()
		for edge in edge_list:
			node_id, reference_id = edge
			self.G.add_edge(node_id, reference_id)

		for node_id, node_record in self.node_records.items():
			if node_id in self.G.nodes:
				nx.set_node_attributes(self.G, {node_id: {"article_title": node_record["title"]}})
		print("Number of nodes in the graph: ", len(self.G.nodes))
		return self.G

class Partition:
	"""
	A class encapsulating the different views of a network partition, along with methods to manipulate the views.

	Attributes
	----------
	G : networkx graph
		The graph whose partition the current object stores
	algorithm: str
		The algorithm used for community detection. Louvain or OSLOM.
	algorithm_datapath: str
		Path to algorithm specific input data format and/or implementations.
		1. For Louvain, this is not requied.
		2. For OSLOM, this is the path to the file containing the partition
		3. For Infomap, this is the path to the file containing the partition
		4. For Directed Louvain, this is the that stores the DirectedLouvain implementation, i.e., it should contain the bin folder
	nodeview : dictionary
		A dictionary describing a partition by mapping nodes to partition labels. Example: {node_1: label_1, ..., node_k: label_k}
	labelview : dictionary
		A dictionary describing a partition by mapping partition label to a list of nodes belonging to that partition. Example: {label_1: [list of label_1 nodes], ..., label_k: [list of label_k nodes]}
	"""

	def __init__(self, G, rand, algorithm, algorithm_datapath = None, out_filepath_suffix = None):
		
		self.G = G
		self.algorithm = algorithm

		if self.algorithm == "louvain":
			self.nodeview = community_louvain.best_partition(self.G, random_state = rand)
			self.labelview = self.node_to_label_view()
			self.sort_labelview()
			self.reassign_labels()
		if self.algorithm == "oslom":
			self.partition_filepath = partition_filepath
			self.labelview = self.labelview_from_file(self.partition_filepath)
			self.nodeview = self.label_to_node_view()
		if self.algorithm == "infomap":
			self.partition_filepath = partition_filepath
			self.nodeview = self.nodeview_from_file(self.partition_filepath)
			self.labelview = self.node_to_label_view()
			self.sort_labelview()
			self.reassign_labels()
		if self.algorithm == "louvain_dir":
			print("Implementing Partition through directed Louvain")
			# If louvain_directed algorithm is to be used, the algorithm_datapath argument to the constructor should be such that it contains the bin folder.
			directed_louvain_binpath = os.path.join(algorithm_datapath, "bin")

			convert_script = os.path.join(directed_louvain_binpath, 'convert')
			community_script = os.path.join(directed_louvain_binpath, 'community')
			hierarchy_script = os.path.join(directed_louvain_binpath, 'hierarchy')

			out_directory = os.path.join(algorithm_datapath, "Output" + "_" + str(out_filepath_suffix))
			if not os.path.exists(out_directory):
				os.makedirs(out_directory)
			graph_txtfile = os.path.join(out_directory, 'renumbered_graph.txt')
			graph_binfile = os.path.join(out_directory, 'graph.bin')
			graph_partition_treefile = os.path.join(out_directory, 'graph.tree')
			graph_partition_communityfile = os.path.join(out_directory, 'graph_communities')
			community_errorlogfile = os.path.join(out_directory, "error_log.txt")

			self.node_renumber(graph_txtfile)

			# Template: ./convert -i graph.txt -o graph.bin
			command = [convert_script] + ['-i'] + [graph_txtfile] + ['-o'] + [graph_binfile]
			subprocess.run(command)

			# Template: ./community graph.bin -l -1 -v > graph.tree
			options = ['-l', '-1', '-v', '-s', '1']
			command = [community_script] + [graph_binfile] + options
			with open(graph_partition_treefile, 'w') as f, open(community_errorlogfile, 'w') as f_err:
				subprocess.run(command, stdout = f, stderr = f_err)

			# Extracting the highest level of community detection from the errorlogfile.
			for line in reversed(open(community_errorlogfile).readlines()):
				if "level"in line:
					max_level = line.rstrip().strip(":").split()[1]
					break

			# Template: ./hierarchy graph.tree -l 2 > graph_node2comm_level2
			options = ['-l', str(max_level)]
			command = [hierarchy_script] + [graph_partition_treefile] + options
			with open(graph_partition_communityfile, 'w') as f:
				subprocess.run(command, stdout = f)

			self.partition_filepath = graph_partition_communityfile
			nodeview_renumbered = self.nodeview_from_file(self.partition_filepath)
			self.nodeview = {}
			for node in nodeview_renumbered:
				if node == 0:
					continue
				node_original = self.reverse_renumber_dict[node]
				self.nodeview[node_original] = nodeview_renumbered[node]
			self.labelview = self.node_to_label_view()
			self.sort_labelview()
			self.reassign_labels()

	def node_renumber(self, renumber_filepath):
		count = 1
		self.renumber_dict = {}
		self.reverse_renumber_dict = {}
		for node in sorted(list(self.G.nodes)):
			self.renumber_dict[node] = count
			self.reverse_renumber_dict[count] = node
			count += 1
			
		with open(renumber_filepath, 'w') as f:
			for edge in self.G.edges:
				node_1 = self.renumber_dict[edge[0]]
				node_2 = self.renumber_dict[edge[1]]
				##print(node_1, node_2)
				f.write("{node1} {node2}\n".format(node1 = node_1, node2 = node_2))
		
	def node_to_label_view(self):
		"""Assumes the calling object has a populated node view; uses this label view to construct and populate the corresponding label view."""
		labelview_dict = {}
		for node, label in self.nodeview.items():
			if label not in labelview_dict:
				labelview_dict[label] = []
			labelview_dict[label].append(node)
		return labelview_dict

	def label_to_node_view(self):
		"""Assumes the calling object has a populated label view; uses this label view to construct and populate the corresponding node view."""
		nodeview_dict = {}
		for label, nodelist in self.labelview.items():
			for node in nodelist:
				nodeview_dict[node] = label
		return nodeview_dict

	def labelview_from_file(self, filepath):
		labelview = {}
		label = -1
		nodelist = []
		with open (filepath, 'r') as f:
			for line in f:
				if line[0] == '#':
					label = int(line.split()[1])
				else:	
					nodelist = list(map(int, line.split()))
					labelview[label] = nodelist
		return labelview

	def nodeview_from_file(self, filepath):
		nodeview = {}
		with open(filepath, 'r') as f:
			for line in f:
				line_values = line.split()
				node = int(line_values[0])
				label = int(line_values[1])
				nodeview[node] = label
		return nodeview

	def sort_labelview(self):
		""" 
		Modifies the labelview; sorts each component of the partition (in the labelview) by degree.
		The modified labelview is a dictionary describing a partition by mapping partition label to a list of nodes belonging to that partition, such that each list is sorted in descending order by node degree.

		"""
		sorted_labelview_dict = {}
		for component_label, component in self.labelview.items():
			sorted_component = sorted(component, key = self.G.degree, reverse = True)
			sorted_labelview_dict[component_label] = sorted_component
		self.labelview = sorted_labelview_dict

	def reassign_labels(self):
		""" 
		Reassigns component labels (in both the labelview and the nodeview) such that lower labels correspond to larger components.
		Example: If the original labelview is {0: [1, 2, 3], 1: [4, 5, 6, 7], 2: [8, 9]}, the output labelview will be the dict {0: [4, 5, 6, 7], 1: [1, 2, 3], 2: [8, 9]}. Correspondingly, modifies the original nodeview ({1:0, 2:0, .... 8:2, 9:2}) to match the labels as in the new labelview ({4:0, 5:0, ... 8:2, 9:2})
		"""

		# reassigned_dict is the new labelview such that lower labels correspond to larger components.
		reassigned_dict = {}
		components_sorted = sorted(self.labelview.values(), key = len, reverse = True)
		for i, component in enumerate(components_sorted):
			reassigned_dict[i] = component	

		# reassigning labels for the nodeview
		for label, component in reassigned_dict.items():
			for node in component:
				self.nodeview[node] = label
		print(self.nodeview)

		self.labelview = reassigned_dict


	def dict_to_list(component_dict):
		component_list = []
		for label in component_dict:
			component_list.append(component_dict[label])
		return component_list

def outofcommunity_edges(subgraph, graph):
	num_edges = 0	#number of edges going out of the subgraph/community
	for node in subgraph.nodes:
		adj_dict = graph[node]
		for adj_node in adj_dict:
			if adj_node not in subgraph:
				num_edges += 1
	return num_edges

def incommunity_edges(subgraph):
	return len(subgraph.edges)

def write_components_to_csv(filePath, labelview_dict, g):
	with open(filePath, 'w', newline='') as csvfile:
		csv_writer = csv.writer(csvfile)
		csv_writer.writerow(["component_label", "node_id", "article_title", "degree"])
		for component_label in sorted(labelview_dict.keys()): 
			component = labelview_dict[component_label]
			for node in component:
				csv_writer.writerow([component_label, node, g.nodes[node]['article_title'], g.degree[node]])
			csv_writer.writerow(['.............', '............'])

def plot_graph(G):
	pos = nx.fruchterman_reingold_layout(G)
	label_dict = dict([(node, str(node)) for node in G.nodes()])
	widths = nx.get_edge_attributes(G, 'weight')

	nx.draw_networkx_nodes(G, pos,
						   nodelist=G.nodes(),
						   node_size=500,
						   node_color='black',
						   alpha=0.7)
	nx.draw_networkx_edges(G, pos, connectionstyle='arc3, rad = 0.1',
						   edgelist = widths.keys(),
						   width=[adjusted_width / 25 for adjusted_width in list(widths.values())],
						   edge_color='orange',
						   alpha=0.6)
	nx.draw_networkx_labels(G, pos=pos,
							labels=label_dict,
							font_color='white')

	plt.show()


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('sourceFilePath', type = str, help = "Path to the Aminer json file or the extracted node file")
	parser.add_argument('destinationDirectoryPath', type = str, help = "Path to the destination (cluster) directory")
	parser.add_argument('algorithm', type = str, help = "Community detection algorithm. Choose from louvain and oslom")
	parser.add_argument('algorithm_datapath', type = str, help = "Path to algorithm specific input data format and/or implementations")
	parser.add_argument('nodeIdPath', nargs = '?', default = None)
	parser.add_argument("--skip_extraction", default = False, action = 'store_true', help = "True if nodes have already been extracted from Aminer. In this case, the path argument gives the path to the extracted file. False by default.")
	
	args = parser.parse_args()
	sourceFilePath = args.sourceFilePath
	destinationDirectoryPath = args.destinationDirectoryPath
	algorithm = args.algorithm
	algorithm_datapath = args.algorithm_datapath
	skip_extraction = args.skip_extraction
	nodeIdPath = args.nodeIdPath

	if not os.path.exists(destinationDirectoryPath):
		os.makedirs(destinationDirectoryPath)

	G = GraphGenerator(sourceFilePath, skip_extraction, nodeIdPath)
	g = G.generate_network()

	partition_main = Partition(g, 1, algorithm, algorithm_datapath)
	print(partition_main.nodeview)
	# print ("Modularity: ", community_louvain.modularity(partition_main.nodeview, g))

	filePath = os.path.join(destinationDirectoryPath, "main.csv")
	write_components_to_csv(filePath, partition_main.labelview, g)

	if algorithm in ["louvain", "louvain_dir"]:
		for component_label, component in partition_main.labelview.items():
			subgraph_g = g.subgraph(component)
			partition_sub = Partition(subgraph_g, 1, "louvain_dir", algorithm_datapath, component_label)
			filePath = os.path.join(destinationDirectoryPath, "component_" + str(component_label) + ".csv")
			write_components_to_csv(filePath, partition_sub.labelview, subgraph_g)


	edgeRatio_filePath = os.path.join(destinationDirectoryPath, "edgeratios.csv")
	with open(edgeRatio_filePath, 'w', newline='') as edge_csvfile:
		edge_csv_writer = csv.writer(edge_csvfile)
		edge_csv_writer.writerow(["Component label", "Within community edges [IN]", "Out of community edges [OUT]", "IN / (IN + OUT)"])
		for component_label, component in partition_main.labelview.items():
			subgraph_g = g.subgraph(component)
			in_edges = incommunity_edges(subgraph_g)
			out_edges = outofcommunity_edges(subgraph_g, g)
			edge_csv_writer.writerow([component_label, in_edges, out_edges, in_edges/(in_edges + out_edges)])

	induced = community_louvain.induced_graph(partition_main.nodeview, g)

	num_nodes_induced = len(induced.nodes)
	header_list = [str(i) for i in range(num_nodes_induced)]
	adjacency_matrix_induced = nx.linalg.graphmatrix.adjacency_matrix(induced, nodelist = range(num_nodes_induced)).toarray()
	edgeWeights_filePath = os.path.join(destinationDirectoryPath, "edgeweights.csv")
	adj_matrix_df = pd.DataFrame(data = adjacency_matrix_induced, index = header_list, columns = header_list)
	adj_matrix_df.to_csv(edgeWeights_filePath)
	#np.savetxt(edgeWeights_filePath, adjacency_matrix_induced, delimiter = ",", header = column_header)

	plot_graph(induced)

if __name__ == '__main__':
	main()