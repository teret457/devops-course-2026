"""Private authentication helper for the local lab. No values are printed."""
from pathlib import Path
import urllib.request,urllib.error,json,base64,subprocess
base=Path('/home/devops/labs13-16/artifactory')
values=json.loads((base/'.secrets.json').read_text())
URL='http://127.0.0.1:18082'
password=values['admin_password']
def request(path,body=None,method=None,auth=True):
 headers={'Content-Type':'application/json'}
 if auth:headers['Authorization']='Basic '+base64.b64encode(('admin:'+password).encode()).decode()
 q=urllib.request.Request(URL+path,data=None if body is None else json.dumps(body).encode(),headers=headers,method=method)
 with urllib.request.urlopen(q,timeout=30) as f:return f.status,f.read()
def login():
 authdir=Path('/home/devops/labs13-16/.docker-auth');authdir.mkdir(exist_ok=True,mode=0o700)
 r=subprocess.run(['docker','--config',str(authdir),'login','127.0.0.1:15000','-u','admin','--password-stdin'],input=password,text=True,capture_output=True)
 print('Docker login exit:',r.returncode);r.check_returncode()
 for p in authdir.iterdir():p.chmod(0o600)
if __name__=='__main__':login()
