import subprocess,json
refs=['127.0.0.1:15000/docker-local/student-demo:1.0','127.0.0.1:15000/docker/student-demo:1.0']
images=json.loads(subprocess.check_output(['docker','image','inspect',*refs],text=True))
for label,im in zip(['LOCAL','VIRTUAL'],images):
 print(label);print('Image ID:',im['Id'])
 for ref in im.get('RepoDigests',[]):
  if ('docker-local/' in ref)==(label=='LOCAL'):print('Repo digest:',ref.split('@')[-1])
assert images[0]['Id']==images[1]['Id']
print('MATCH: identical content identifiers')
