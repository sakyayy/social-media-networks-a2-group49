import pandas as pd
import networkx as nx

def loadData():
    df = pd.read_json("cleanComments.json")

    return df

def cleanNetworkData():
    df = loadData()
    # removing deleted or null rows of data 
    df = df.dropna(subset=["author", "comment_id", "parent_id", "body", "post_id"])
    df = df[df["author"] != "[deleted]"]
    df = df[df["author"] != "[removed]"]

    return df

def buildNetwork():
    df = cleanNetworkData()

    # building normal reply graph
    replyGraph = nx.DiGraph()
    # get dictionary mapping threads to the authors that created them 
    threadToAuthor = dict(df[df["is_submitted"] == True].groupby("thread_id")["author"].first())
    idToAuthor = dict(zip(df["comment_id"], df["author"]))

    # getting the number of threads is submitted by each author
    thread_counts = pd.Series(threadToAuthor).value_counts().to_dict()

    # looping through unique authors and adding a node for them
    # incl. count of threads submitted by the author to analyse how involved they are
    for user in df["author"].unique():
        replyGraph.add_node(user, numThreads=thread_counts.get(user, 0))

    # iterate through each row
    for _, row in df.iterrows():
        # hold data we need
        user = row["author"]
        comment_id = row["comment_id"]
        parent_id = row["parent_id"]
        subreddit = row["subreddit"]
        body = row["body"]
        thread_id = row["post_id"]
        score = row["score"]

        # check if comment is replying to original post or another user
        if parent_id == "t3_" + thread_id:
            parent_user = threadToAuthor.get(thread_id)
        else:
            parent_comment_id = parent_id.replace("t1_", "")
            parent_user = idToAuthor.get(parent_comment_id)
        
        # check that the parent user exists first 
        if parent_user:
            # checking that the parent user is not replying to themselvees coz we don't want loops 
            if parent_user != user:
                # check if edge already exists
                if(replyGraph.has_edge(user, parent_user)):
                    # add weight of how many times the user has replied to the same author
                    replyGraph[user][parent_user]["numReplies"] += 1
                else:
                    replyGraph.add_edge(user, parent_user, numReplies=1)
    
    return replyGraph

def calcNetworkStats():
    replyGraph = buildNetwork()
    
    # getting graph stats
    num_nodes = replyGraph.number_of_nodes()
    num_edges  = replyGraph.number_of_edges()

    density = nx.density(replyGraph)
    # both the same value
    avg_in_degree = num_edges / num_nodes 
    avg_out_degree = num_edges / num_nodes

    num_strong_components = len(list(nx.strongly_connected_components(replyGraph)))
    num_weak_components = len(list(nx.weakly_connected_components(replyGraph)))
    # get the size of the largest weakly connected component 
    # to see how connected/disconnected the graph is

    if num_nodes > 0:
        largest_wcc = max(nx.weakly_connected_components(replyGraph), key=len)
        largest_wcc_size = len(largest_wcc)
    else:
        largest_wcc_size = 0

    reciprocity = nx.reciprocity(replyGraph);
    transitivity = nx.transitivity(replyGraph)

    undir_replyGraph = replyGraph.to_undirected()
    # avg_clusterring = 


