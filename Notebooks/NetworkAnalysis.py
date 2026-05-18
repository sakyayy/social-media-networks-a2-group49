import pandas as pd
import networkx as nx

fJsonName = "cleanComments.json"
df = pd.read_json("cleanComments.json")

# building normal reply graph
replyGraph = nx.DiGraph()
# get dictionary mapping threads to the authors that created them 
threadToAuthor = dict(df[df["is_submitted"] == True].groupby("thread_id")["author"].first())
idToAuthor = dict(df["comment_id"], df["author"])

# getting the number of threads is submitted by each author
thread_counts = pd.series(threadToAuthor).value_counts().to_dict()

# looping through unique authors and adding a node for them
# incl. count of threads submitted by the author to analyse how involved they are
for user in df["author"].unique:
    replyGraph.add_node(user, numThreads=int(thread_counts))

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
    if parent_id == thread_id:
        parent_user = threadToAuthor.get(thread_id)
    else:
        parent_user = idToAuthor.get(parent_id)
    
    # check that the parent user exists first 
    if parent_user:
        # checking that the parent user is not replying to themselvees coz we don't want loops 
        if parent_user != user:
            # check if edge already exists
            if(replyGraph.has_edge(user, parent_user)):
                # add weight of how many times the user has replied to the same author
                replyGraph.add_edge(user, parent_user, numReplies=+ 1)
            else:
                replyGraph.add_edge(user, parent_user, numReplies=1)







            


    





