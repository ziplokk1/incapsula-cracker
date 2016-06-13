import logging
from incapsula import crack, IncapSession
import requests

logging.basicConfig(level=10)


session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0'})
# r = crack(session, session.get('https://www.whoscored.com'))
r = session.get('https://www.whoscored.com')
print r.content
