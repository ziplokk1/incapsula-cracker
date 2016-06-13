import logging
from incapsula import crack, IncapSession
import requests

logging.basicConfig(level=10)


session = requests.Session()
# r = crack(session, session.get('https://www.whoscored.com'))
r = session.get('https://www.whoscored.com')
print r.content
