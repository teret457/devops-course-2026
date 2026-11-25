"""Generate private initial configuration; does not accept licenses or start services."""
import json,secrets
from pathlib import Path
base=Path('/home/devops/labs13-16/artifactory');base.mkdir(parents=True,exist_ok=True)
p=base/'.secrets.json'
if not p.exists():
 p.write_text(json.dumps({'db_password':secrets.token_urlsafe(32),'admin_password':'Aa1'+secrets.token_urlsafe(32)}));p.chmod(0o600)
v=json.loads(p.read_text())
p=base/'.db.env'
p.write_text('POSTGRES_USER=artifactory\nPOSTGRES_DB=artifactorydb\nPOSTGRES_PASSWORD='+v['db_password']+'\n');p.chmod(0o600)
p=base/'system.yaml'
if p.exists():raise SystemExit('Configuration already exists; preserved. Apply intentional edits manually.')
p.write_text('shared:\n  database:\n    type: postgresql\n    driver: org.postgresql.Driver\n    url: jdbc:postgresql://lab13-db:5432/artifactorydb\n    username: artifactory\n    password: '+v['db_password']+'\n  extraJavaOpts: "-Xms256m -Xmx768m -XX:ActiveProcessorCount=1 -XX:UseAVX=0 -XX:TieredStopAtLevel=1"\njfconnect:\n  enabled: false\n');p.chmod(0o600)
print('Private initialization files generated; passwords are not displayed.')
