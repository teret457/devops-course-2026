"""Recover stopped JCR processes after a slow local VM start. No credentials printed."""
import json,subprocess,time,urllib.request
CONTAINER='lab13-artifactory'
def execute(args,**kw):return subprocess.run(args,check=True,**kw)
def running(needle):
 data=subprocess.check_output(['docker','exec',CONTAINER,'ps','-eo','args'],text=True)
 return any(needle in line for line in data.splitlines())
def start(binary,extra=None,args=None):
 if running(binary):print('Already running:',binary.rsplit('/',1)[-1]);return
 host=json.loads(subprocess.check_output(['docker','inspect',CONTAINER],text=True))[0]['Config']['Hostname']
 values={'JF_SHARED_NODE_NAME':host,'JF_SHARED_JFROGURL':'http://localhost:8082','JF_SYSTEM_YAML':'/opt/jfrog/artifactory/var/etc/system.yaml'}
 values.update(extra or {})
 command=['docker','exec','-d']
 for k,v in values.items():command+=['-e',k+'='+v]
 execute(command+[CONTAINER,binary]+(args or []));print('Started:',binary.rsplit('/',1)[-1])
if __name__=='__main__':
 ping=subprocess.run(['docker','exec',CONTAINER,'curl','--fail','--max-time','5','-s','http://localhost:8040/access/api/v1/system/ping'],capture_output=True)
 if ping.returncode:raise SystemExit('Access is still starting. Wait and run recovery again; no services were changed.')
 root='/opt/jfrog/artifactory/app/'
 start(root+'router/bin/jf-router',{'JF_ROUTER_SERVICEREGISTRY_ACCESSURL':'http://localhost:8040/access','JF_ROUTER_SERVICEREGISTRY_TOPOLOGYURL':'http://localhost:8020/topology','JF_ROUTER_TOPOLOGY_LOCAL_REQUIREDSERVICETYPES':'jfrt,jfac,jfmd,jffe,jfob,jfcfg,jfevt,jftpl,jfbus'})
 for name in ['event','observability','metadata']:
  start(root+name+'/bin/jf-'+name,{'JF_'+name.upper()+'_ACCESSCLIENT_URL':'http://localhost:8046/access'})
 if not running(root+'frontend/bin/server/dist/bundle.js'):
  start(root+'third-party/node/bin/node',{'NODE_ENV':'PRODUCTION'},['--no-enable-fips',root+'frontend/bin/server/dist/bundle.js',root+'frontend'])
 for _ in range(10):
  try:
   with urllib.request.urlopen('http://127.0.0.1:15000/router/api/v1/system/readiness',timeout=3) as response:
    if response.status==200:print('Registry readiness HTTP 200');break
  except Exception:pass
  time.sleep(3)
 else:raise SystemExit('Processes started. Registry is still initializing; inspect logs and repeat readiness check.')
