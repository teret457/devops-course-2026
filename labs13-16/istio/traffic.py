import requests,collections,sys
count=collections.Counter()
for _ in range(int(sys.argv[1]) if len(sys.argv)>1 else 30):
 r=requests.get('http://reviews:9080/reviews/0',timeout=15)
 if r.status_code!=200:count['HTTP '+str(r.status_code)]+=1;continue
 j=r.json();name=j.get('podname','unknown');version=name.split('-')[1] if name.startswith('reviews-') else name
 count[version]+=1
print('Requests:',sum(count.values()))
for k,v in sorted(count.items()):print(k,':',v)
