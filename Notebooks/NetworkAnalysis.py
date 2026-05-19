import pandas as pd
import networkx as nx
import community 
import csv 
from collections import Counter
import matplotlib as plt

def loadData():
    df = pd.read_json("cleanComments.json")

    return df

def cleanNetworkData(df):
    # removing deleted or null rows of data 
    df = df.dropna(subset=["author", "comment_id", "parent_id", "body", "post_id", "parent_author"])
    df = df[df["author"] != "[deleted]"]
    df = df[df["author"] != "[removed]"]

    df = df[df["parent_author"] != "[deleted]"]

    return df

def buildNetwork(df):

    # building normal reply graph
    replyGraph = nx.DiGraph()

    # changed to: loop through all users incl. parent_author to add nodes
    all_users = set(df["author"]).union(set(df["parent_author"]))
    for user in all_users:
        replyGraph.add_node(user)

    # iterate through each row
    for _, row in df.iterrows():
        # hold data we need
        user = row["author"]
        parent_user = row['parent_author']
        
        # check that the parent user exists first 
        if parent_user:
            # checking that the parent user is not replying to themselvees coz we don't want loops 
            if parent_user != user:
                # check if edge already exists
                if(replyGraph.has_edge(user, parent_user)):
                    # add weight of how many times the user has replied to the same author
                    replyGraph[user][parent_user]["weight"] += 1
                else:
                    replyGraph.add_edge(user, parent_user, weight=1)
    
    return replyGraph

def calcNetworkStats(replyGraph):
    
    # getting graph stats
    num_nodes = replyGraph.number_of_nodes()
    num_edges  = replyGraph.number_of_edges()

    density = nx.density(replyGraph)
    # both the same value
    avg_in_degree = num_edges / num_nodes if num_nodes > 0 else 0
    avg_out_degree = num_edges / num_nodes if num_nodes > 0 else 0

    num_strong_components = len(list(nx.strongly_connected_components(replyGraph)))
    num_weak_components = len(list(nx.weakly_connected_components(replyGraph)))
    # get the size of the largest weakly connected component 
    # to see how connected/disconnected the graph is

    if num_nodes > 0:
        largest_wcc = max(nx.weakly_connected_components(replyGraph), key=len)
        largest_wcc_size = len(largest_wcc)
    else:
        largest_wcc_size = 0
    
    # needed to get avg clusterring and transitivity
    undir_replyGraph = replyGraph.to_undirected()

    reciprocity = nx.reciprocity(replyGraph)
    transitivity = nx.transitivity(undir_replyGraph)

    avg_clusterring = nx.average_clustering(undir_replyGraph)

    stats = {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "density": density,
        "avg_in_degree": avg_in_degree,
        "avg_out_degree": avg_out_degree,
        "num_strong_components": num_strong_components,
        "num_weak_components": num_weak_components,
        "largest_wcc_size": largest_wcc_size,
        "reciprocity": reciprocity,
        "transitivity": transitivity,
        "avg_clusterring": avg_clusterring
    }

    dfstats = pd.DataFrame([stats])
    dfstats.to_csv("network_stats.csv", index=False)

    # write into graph 
    nx.write_graphml(replyGraph, "replyGraph.graphml")
    return dfstats #returning csv file of graphml stats

# replygraph = graphml file 
def calcCentrality(fileName):

    replyGraph = nx.readwrite.read_graphml(fileName)

    # in and ouit degree centrality
    in_degree_cent = nx.in_degree_centrality(replyGraph)
    out_degree_cent = nx.out_degree_centrality(replyGraph)

    # betweenness
    betweenness_centrality = nx.betweenness_centrality(replyGraph)

    # eigen vector 
    eigen_vector_cent = nx.eigenvector_centrality_numpy(replyGraph)

    # katz centrality
    # added base value of 1 
    katz_centrality = nx.katz_centrality_numpy(replyGraph, beta=1.0)

    centrality_scores = {
        "in_degree_cent": in_degree_cent,
        "out_degree_cent": out_degree_cent,
        "betweenness_centrality": betweenness_centrality,
        "eigen_vector_cent": eigen_vector_cent,
        "katz_centrality": katz_centrality
    }

    dfcentrality_scores = pd.DataFrame([centrality_scores])
    dfcentrality_scores.to_csv("centrality_scores.csv", index=False)

    return dfcentrality_scores

def detectCommunities(fileName):
    replyGraph = nx.readwrite.read_graphml(fileName)
    # make graph undirected
    modGraph = nx.to_undirected(replyGraph)

    # louvain 
    louvain_comms = community.best_partition(modGraph)
    modularity_score = community.modularity(louvain_comms, modGraph)

    community_sizes = []
    # assign louvain comm for each node
    for node, comm in louvain_comms.items():
        replyGraph.nodes[node]["community"] = comm
    
    dfcomm_assignments = pd.DataFrame([
        {"user": node, "community": comm}
        for node, comm in louvain_comms.items()
    ])
    
    # get size of the dif communities
    community_sizes = Counter(louvain_comms.values())

    # save communities and their sizes to a df
    dfcomm_size = pd.DataFrame([
        {"community": comm, "size": size}
        for comm, size in community_sizes.items()
    ])
    # save modularity score and num of communities to a separate df
    dfstats = pd.DataFrame([{
        "modularity_score": modularity_score,
        "num_communities": len(community_sizes)
    }])
    
    dfcomm_assignments.to_csv("community_assignments.csv", index=False)
    dfcomm_size.to_csv("community_sizes.csv", index=False)
    dfstats.to_csv("community_stats.csv", index=False)

    return dfcomm_assignments, dfcomm_size, dfstats

# plot basic graphs
# using gephi for better ones tho
def visualiseNetwork(fileName, dfcentrality, dfcomm_size, dfcomm_assignments, dfcomm_stats):
    in_degree_cent = dfcentrality["in_degree_cent"]
    out_degree_cent = dfcentrality["out_degree_cent"]
    betweenness_cent = dfcentrality["betweenness_centrality"]
    eigen_cent = dfcentrality["eigen_vector_cent"]
    katz_cent = dfcentrality["katz_centrality"]

    # centrality plots
    # plotting all three in one for better comparison
    plt.figure()
    plt.subplot(1, 3, 1)
    plt.hist(in_degree_cent)
    plt.title("in-degree centrality")
    plt.xlabel("type")

    plt.subplot(1, 3, 2)
    plt.hist(out_degree_cent)
    plt.title("out-degree centrality")
    plt.xlabel("type")

    plt.subplot(1, 3, 3)
    plt.hist(betweenness_cent)
    plt.title("betweenness centrality")
    plt.xlabel("type")


    # katz and eigen vector
    # same way of plotting ao its easier, will be using gephi or better visualisations tho
    plt.figure()
    plt.subplot(1, 2, 1)
    plt.hist(eigen_cent)
    plt.title("eigen vector centrality")
    plt.xlabel("type")

    plt.subplot(1, 2, 2)
    plt.hist(katz_cent)
    plt.title("katz centrality")
    plt.xlabel("type")

    # community plots
    # gtting top 10 communities
    top_communities = dfcomm_size.sort_values("size", ascending=False).head(10)

    plt.figure()
    plt.bar(top_communities["community"].astype(str), top_communities["size"])
    plt.title("top 10 Louvain community sizes")
    plt.xlabel("community")
    plt.ylabel("number of users")
    
    plt.show()











