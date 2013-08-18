import yql
from yql.storage import FileTokenStore
from yahoo_credentials import *
import os


def q(query):
    y3 = yql.ThreeLegged(YAHOO_CONSUMER_KEY, YAHOO_CONSUMER_SECRET)
    token = get_token()
    return y3.execute(query, token=token)

def get_token():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'cache'))
    token_store = FileTokenStore(path, secret=YAHOO_STORAGE_SECRET)
    stored_token = token_store.get('josh')
    y3 = yql.ThreeLegged(YAHOO_CONSUMER_KEY, YAHOO_CONSUMER_SECRET)
    if stored_token is None:
        query = 'select * from social.connections where owner_guid=me'
        request_token, auth_url = y3.get_token_and_auth_url()
        print "Go to {0}".format(auth_url)
        verifier = raw_input("Please put in token that Yahoo gives you")
        access_token = y3.get_access_token(request_token, verifier)
        token_store.set('josh', access_token)
        return access_token
    else:
        token = y3.check_token(stored_token)
        if token != stored_token:
            token_store.set('josh', token)
        return token
if __name__ == "__main__":
    get_token()