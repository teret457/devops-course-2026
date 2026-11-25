"""Public, secret-free summary of the three Docker repositories."""
from configure13 import request
import json
_,raw=request('/artifactory/api/repositories')
for v in json.loads(raw):
 if v['key'] in ('docker','docker-local','docker-remote'):
  print(v['key'],v['type'],v.get('packageType','Docker'))
_,raw=request('/artifactory/api/system/version');print(raw.decode())
