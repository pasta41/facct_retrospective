import networkx as nx
import networkx.algorithms.community as nx_comm
import csv
import chart_studio.plotly as py
from plotly.graph_objs import *
from plotly.offline import iplot
import argparse

#python3 construct_graph.py --s "/home/sameer/Projects/Political-leaning/Data/TXTs/titles.csv" --r "/home/sameer/Projects/Political-leaning/Data/TXTs/combined-final.csv" --f 0 --d "/home/sameer/Projects/Political-leaning/Data/TXTs/clusters.csv"

def edge_to_remove(g):
    d1 = nx.edge_betweenness_centrality(g, weight = "weight") 
    list_of_tuples = list(d1.items()) 
    
      
    sorted_list_of_tuples = sorted(list_of_tuples, key = lambda x:x[1], reverse = True) 
    # Will return in the form (a,b) 
    return sorted_list_of_tuples[0][0] 

def girvan(g, k):
    a = nx.connected_components(g) 
    lena = len(list(a)) 
    print (' The number of connected components is ', lena) 
    while (lena < k): 
  
        # We need (a,b) instead of ((a,b)) 
        u, v = edge_to_remove(g) 
        g.remove_edge(u, v)  
          
        a = nx.connected_components(g) 
        lena = len(list(a)) 
        print (' The number of connected components is ', lena) 
    a = list(sorted(nx.connected_components(g), key = len, reverse = True))
    components_sorted = []
    for component in a:
    	sources = [node for node in component if int(node) < 1000]
    	sources = sorted(sources, key = g.degree, reverse = True)
    	destinations = [node for node in component if int(node) >= 1000]
    	destinations = sorted(destinations, key = g.degree, reverse = True)
    	components_sorted.append(sources + destinations)
    #print(components_sorted)
    return components_sorted

def generate_node(record):
	node_attributes = {}
	node_attributes["id"] = record[1] 

def get_title_dictionary(title_file):
	with open(title_file) as titlefile:
		reader = csv.reader(titlefile)
		title_dict = {}
		for row in reader:
			title_dict[row[0]] = row[1]
	return title_dict

def get_node_text(G):
	reference_articles_titles = [G.nodes[node]['articleTitle'] if 'articleTitle' in G.nodes[node] else 'none' for node in G.nodes()]
	reference_articles_authors = [G.nodes[node]['authors'] if 'authors' in G.nodes[node] else 'none' for node in G.nodes()]
	node_text = ['Title: {title}\nAuthors: {author}'.format(title = title, author = author) for title, author in zip(reference_articles_titles, reference_articles_authors)]
	return node_text

def construct_graph(title_file, reference_csv, facct_flag):
	G = nx.Graph()
	title_dict = get_title_dictionary(title_file)
	reader = csv.reader(reference_csv)
	prev_ref_id = -1
	for row in reader:
		add_flag = 0
		if row[1] == "Id":
			continue
		source_id = row[1]
		reference_id = row[7]

		if source_id not in G:
			source_filename = row[2]
			source_title = title_dict[source_filename]
			G.add_node(source_id, articleTitle = source_title)

		if (int(reference_id) < 1000) or (int(reference_id) >= 1000 and reference_id == prev_ref_id):
			add_flag = 1
		if reference_id not in G and add_flag == 1:
			G.add_node(reference_id, articleTitle = row[4], authors = row[3], venue = row[5], year = row[6])
		prev_ref_id = reference_id
			
		if add_flag == 1:
			if int(reference_id) < 1000:
				G.add_edge(source_id, reference_id, weight = 1)
			else:
				G.add_edge(source_id, reference_id, weight = 1)
	return G

def plot_graph(G):
	pos = nx.fruchterman_reingold_layout(G)		#returns a dictionary of positions keyed by node
	Xv = [pos[k][0] for k in G.nodes()]
	Yv = [pos[k][1] for k in G.nodes()]
	Xed = []
	Yed = []

	node_text = get_node_text(G)
	
	for edge in G.edges():
	    Xed += [pos[edge[0]][0], pos[edge[1]][0], None]
	    Yed += [pos[edge[0]][1], pos[edge[1]][1], None]

	edge_trace = Scatter(x=Xed,
	               y=Yed,
	               mode='lines',
	               line=dict(color='rgb(210,210,210)', width=1),
	               hoverinfo='none'
	               )
	node_trace = Scatter(x=Xv,
	               y=Yv,
	               mode='markers',
	               name='net',

	               marker=dict(symbol='circle-dot',
	                             size=5,
	                             color='#6959CD',
	                             line=dict(color='rgb(50,50,50)', width=0.5)
	                           ),
	               text=node_text,
	               hoverinfo='text'
	               )

	node_trace.marker.size = [in_deg[1] for in_deg in G.in_degree()]

	data1 = [edge_trace, node_trace]
	fig1 = Figure(data = data1, layout = None)
	iplot(fig1, filename = 'citation-network')

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--s", dest = 'sourceTitleFile', type = str, help = "Path to the file mapping source filenames to article titles")
	parser.add_argument("--r", dest = 'referenceFile', type = str, help = "Path to the reference file")
	parser.add_argument("--d", dest = 'destinationFile', type = str, help = "Path to the destination file")
	parser.add_argument("--f", dest = 'facctFlag', type = int, help = "Boolean set to 1 if graph is to include only FACCT papers")
	parser.add_argument("--k", dest = 'numClusters', type = int, help = "Number of clusters")
	
	args = parser.parse_args()
	destinationFile = args.destinationFile + "_" + str(args.numClusters) + ".csv"

	with open(args.referenceFile) as csvfile:	
		G = construct_graph(args.sourceTitleFile, csvfile, args.facctFlag)
		component_list = girvan(G, args.numClusters) 
		with open(destinationFile, 'w', newline='') as csvfile:
			csv_writer = csv.writer(csvfile)
			for component in component_list: 
			    for node in component:
			    	csv_writer.writerow([node, G.nodes[node]['articleTitle'], G.degree[node]])
			    csv_writer.writerow(['.............', '............']) 
			print(nx_comm.modularity(G, component_list))