# social-media-networks-a2-group49
SMNA assignment 2 code repository

**Group Members:**
- Caroline Forster
- Sangay Pelbar
- Sakina Bayani

## Project Summary

This code collects, cleans, and analyses textual Reddit discussion data from a 2015 Reddit comments dataset. The investigation explores how online political discussion reflects opinions and discourse surrounding US foreign policy across multiple Reddit communities. To conduct this, Reddit comment data collected from multiple political and geopolitical subreddits to perform sentiment analysis, topic analysis, and social network analysis.

The data collection stage extracted:

- comment text
- subreddit information
- author usernames
- parent-child reply relationships
- timestamps
- comment scores

## Project Structure

```text
social-media-networks-a2-group49/
│
├── Notebooks/
│   ├── DataCollection.ipynb
│   ├── DataPreProcessing.ipynb
│   ├── NetworkAnalysis.py
│   │
│   ├── cleanComments.json
│   ├── reddit_edges.csv
│   ├── network_stats.csv
│   ├── community_stats.csv
│   ├── community_sizes.csv
│   ├── community_assignments.csv
│   ├── centrality_scores.csv
│   │
│   ├── replyGraph.graphml
│   ├── mod_replyGraph.graphml
│   │
│   ├── *.png
│
├── README.md
├── .gitignore
```

## Data Source

The project uses the publicly available 2015 Reddit comments dataset in `.bz2` format.

## Required Libraries

- pandas
- nltk
- matplotlib
- json
- bz2
- networkx
- python-louvain

Install required packages using:

```bash
pip install pandas nltk matplotlib networkx python-louvain
```

## Running the files

1. Open the notebooks in Jupyter Notebook or VS Code.

2. Run:
   1. DataCollection.ipynb
   2. DataPreProcessing.ipynb
   3. NetworkAnalysis.py
     - python NetworkAnalysis.py

3. Generated outputs, graphs, and CSV files will appear within the Notebooks/ directory. 

