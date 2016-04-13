import requests
from incapsula import crack

session = requests.Session()
r = crack(session, session.get('http://www.bjs.com'))
print r.content
