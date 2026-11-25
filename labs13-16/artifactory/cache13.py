from configure13 import request
import json
_,raw=request('/artifactory/api/storage/docker-remote-cache/library/alpine/3.21')
j=json.loads(raw)
print('Repository:',j.get('repo'));print('Path:',j.get('path'))
for c in j.get('children',[]):print(c['uri'],'folder' if c['folder'] else 'file')
