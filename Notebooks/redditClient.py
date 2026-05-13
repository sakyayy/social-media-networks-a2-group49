import sys
import praw


def redditClient():
    
try:
        
        clientId = ""
        clientSecret = ""
        password = ""
        userName = ""
        userAgents = 'client for SNAM2026'

        redditClient = praw.Reddit(client_id = clientId,
                                   client_secret = clientSecret,
                                   password = password,
                                   username = userName,
                                   user_agent = userAgents)
    except KeyError:
        sys.stderr.write("Key or secret token are invalid.\n")
        sys.exit(1)


    return redditClient