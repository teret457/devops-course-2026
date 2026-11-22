# Practical work 12

Tereshin Artem, EFBO-14-24. Based on https://habr.com/ru/companies/otus/articles/358588/ and https://github.com/alexellis/hash-browns. Source attribution retained.

Single-host Docker Compose replaces historical Swarm deployment. Build from source because the sample published manifest did not match amd64. Go1.23-alpine and gofmt adapt build, application logic unchanged. Prometheus3.0.1 scrapes every5s. Ports9090 and8080 only loopback. SSH tunnel can expose them locally to the student.

cd monitoring && docker compose -f compose.yml up -d --build

POST /hash computes SHA256; GET /hash gives405 in this source revision, unlike400 discussed in article. Queries: up; rate(hash_seconds_count[1m]); rate(hash_seconds_sum[5m])/rate(hash_seconds_count[5m]); rate(hash_seconds_count{code="405"}[1m]). Stop/start test confirms up0→1.
