# Usage

```
import incapsula
import requests

session = requests.Session()
response = session.get('http://example.com')  # url is blocked by incapsula
response = incapsula.crack(session, response.url, response.content)  # url is no longer blocked by incapsula
```

# Setup

There should be no problems using incapsula-cracker right out of the box.

If there are issues, try the following

* Open incapsula/serialize.html in browser
* Copy and paste the json data into incapsula/navigator.json

# Notes

* config.py, navigator.json, and serialize.html have all only been tested using firefox.
* currently incapsula only works with the requests library. 