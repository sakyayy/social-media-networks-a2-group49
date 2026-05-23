import pandas as pd
import networkx as nx
import community.community_louvain as community
from collections import Counter
import matplotlib.pyplot as plt

mainFileName = "replyGraph.graphml"
modFileName = "mod_replyGraph.graphml"

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
        replyGraph.add_node(user, subreddits=set(), comment_count=0)

    # iterate through each row
    for _, row in df.iterrows():
        # hold data we need
        user = row["author"]
        parent_user = row['parent_author']
        subreddit = row["subreddit"]

        # update node attributes for user
        replyGraph.nodes[user]["subreddits"].add(subreddit)
        replyGraph.nodes[user]["comment_count"] += 1

        # update for parent
        if parent_user in replyGraph.nodes:
            replyGraph.nodes[parent_user]["subreddits"].add(subreddit)
        
        # check that the parent user exists first 
        if parent_user:
            # checking that the parent user is not replying to themselvees coz we don't want loops 
            if parent_user != user:
                # check if edge already exists
                if replyGraph.has_edge(user, parent_user):
                    # add weight of how many times the user has replied to the same author
                    replyGraph[user][parent_user]["weight"] += 1
                else:
                    replyGraph.add_edge(user, parent_user, weight=1)

    for node in replyGraph.nodes:
        subs = replyGraph.nodes[node]["subreddits"]
        replyGraph.nodes[node]["subreddit"] = ", ".join(sorted(subs)) if subs else "unknown";
        del replyGraph.nodes[node]["subreddits"]
    
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
    nx.write_graphml(replyGraph, mainFileName)
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
    try:
        eigen_vector_cent = nx.eigenvector_centrality_numpy(replyGraph)
    except Exception:
        try:
            # max_iter set to 1000 to avoid errors
            eigen_vector_cent = nx.eigenvector_centrality(replyGraph, max_iter=1000)
        except Exception:
            eigen_vector_cent = { user: 0 for user in replyGraph.nodes }

    # katz centrality
    # added base value of 1 
    try:
        katz_centrality = nx.katz_centrality_numpy(replyGraph, beta=1.0)
    except Exception:
        try:
            katz_centrality = nx.katz_centrality(replyGraph, beta=1.0, max_iter=1000)
        except Exception:
            katz_centrality = { user: 0 for user in replyGraph.nodes }

    centrality_scores = []

    for user in replyGraph.nodes:
        centrality_scores.append({
            "user": user,
            "in_degree_cent": in_degree_cent.get(user, 0),
            "out_degree_cent": out_degree_cent.get(user, 0),
            "betweenness_centrality": betweenness_centrality.get(user, 0),
            "eigen_vector_cent": eigen_vector_cent.get(user, 0),
            "katz_centrality": katz_centrality.get(user, 0)
        })

    dfcentrality_scores = pd.DataFrame(centrality_scores)
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
        {"user": node, "community": comm, "subreddit": replyGraph.nodes[node].get("subreddit", "unknown")}
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

    nx.write_graphml(replyGraph, modFileName)

    return dfcomm_assignments, dfcomm_size, dfstats

# plot basic graphs
# using gephi for better ones tho
def visualiseNetwork(dfcentrality, dfcomm_size, dfcomm_assignments):
    in_degree_cent = dfcentrality["in_degree_cent"]
    out_degree_cent = dfcentrality["out_degree_cent"]
    betweenness_cent = dfcentrality["betweenness_centrality"]
    eigen_cent = dfcentrality["eigen_vector_cent"]
    katz_cent = dfcentrality["katz_centrality"]

    # centrality plots
    # plotting all three in one for better comparison
    plt.figure()
    plt.hist(in_degree_cent)
    plt.title("in-degree centrality")
    plt.xlabel("centrality score")
    plt.ylabel("number of users")
    plt.savefig("in_degreeCentrality.png")

    plt.figure()
    plt.hist(out_degree_cent)
    plt.title("out-degree centrality")
    plt.xlabel("centrality score")
    plt.ylabel("number of users")
    plt.savefig("out_degreeCentrality.png")

    plt.figure()
    plt.hist(betweenness_cent)
    plt.title("betweenness centrality")
    plt.xlabel("centrality score")
    plt.ylabel("number of users")
    plt.savefig("betweennes_degreeCentrality.png")


    # katz and eigen vector
    # same way of plotting ao its easier, will be using gephi or better visualisations tho
    plt.figure()
    plt.subplot(1, 2, 1)
    plt.hist(eigen_cent)
    plt.title("eigen vector centrality")
    plt.xlabel("centrality score")
    plt.ylabel("number of users")

    plt.subplot(1, 2, 2)
    plt.hist(katz_cent)
    plt.title("katz centrality")
    plt.xlabel("centrality score")
    plt.ylabel("number of users")
    plt.savefig("eigenKatzCentrality.png")

    # community plots
    # gtting top 10 communities
    top_communities = dfcomm_size.sort_values("size", ascending=False).head(10)

    plt.figure()
    plt.bar(top_communities["community"].astype(str), top_communities["size"])
    plt.title("top 10 Louvain community sizes")
    plt.xlabel("community")
    plt.ylabel("number of users")
    plt.savefig("topCommunities.png")

    # top 10 in degree
    top_in = dfcentrality.sort_values("in_degree_cent", ascending=False).head(10)

    plt.figure()
    plt.bar(top_in["user"], top_in["in_degree_cent"])
    plt.xticks(rotation=45, ha="right")
    plt.title("top 10 users by in-degree")
    plt.xlabel("user")
    plt.ylabel("centrality score")
    plt.tight_layout()
    plt.savefig("top10InDegree.png")

    # top 10 betwenness
    top_in = dfcentrality.sort_values("betweenness_centrality", ascending=False).head(10)

    plt.figure()
    plt.bar(top_in["user"], top_in["betweenness_centrality"])
    plt.xticks(rotation=45, ha="right")
    plt.title("top 10 users - betwenness")
    plt.xlabel("user")
    plt.ylabel("centrality score")
    plt.tight_layout()
    plt.savefig("top10Betweenness.png")

    # top 10 katz
    top_in = dfcentrality.sort_values("katz_centrality", ascending=False).head(10)

    plt.figure()
    plt.bar(top_in["user"], top_in["katz_centrality"])
    plt.xticks(rotation=45, ha="right")
    plt.title("top 10 users - katz centrality")
    plt.xlabel("user")
    plt.ylabel("centrality score")
    plt.tight_layout()
    plt.savefig("top10Katz.png")

    # bar chart for subreddits and community comparioson
    comm_subreddits = (
        dfcomm_assignments.groupby(["community", "subreddit"]).size().reset_index(name="count")
    )

    top_comm_ids = (
        dfcomm_size.sort_values("size", ascending=False).head(5)["community"]
    )

    comm_subreddits = comm_subreddits[comm_subreddits["community"].isin(top_comm_ids)]

    dfpivot = comm_subreddits.pivot(
        index="community",
        columns="subreddit",
        values="count"
    ).fillna(0)

    dfpivot.plot(
        kind="bar",
        stacked=True, 
        figsize=(10, 6)
    )

    plt.title("subreddit composition of top communities")
    plt.xlabel("Community")
    plt.ylabel("number of users")
    plt.tight_layout()
    plt.savefig("commSubredditComposition.png")
    
    plt.show()

def main():
    df = loadData()
    df = cleanNetworkData(df)
    G = buildNetwork(df)
    stats = calcNetworkStats(G)
    centrality = calcCentrality(mainFileName)
    comms, comm_size, comm_stats = detectCommunities(mainFileName)
    visualiseNetwork(centrality, comm_size, comms)

if __name__ == "__main__":
    main()