# Практическая работа 13

Терешин Артем Дмитриевич, ЭФБО-14-24.

Локальный JFrog Container Registry 7.161.15 и PostgreSQL16. Бесплатная редакция JCR, без облачной подписки. Порты доступны только на loopback VM: 18081→8081 и 18082→8082. На Windows UI доступен через SSH-туннель 28082→18082. Docker-клиент обращается к Nginx на 127.0.0.1:15000, который проксирует запросы к Router18082 и сохраняет Host.

## Установка стенда

Фактическая установка выполнена командами Docker, не Helm. `prepare.py` содержит генератор эквивалентной исходной конфигурации: создаёт случайные пароли и файлы0600, не выводит их значения. Он не запускает контейнеры и не принимает соглашения.

На новом стенде создайте каталог `~/labs13-16/artifactory/var/etc`, сеть lab13 и том lab13_pg. Скопируйте подготовленный system.yaml в var/etc с владельцем1030:1030 и режимом0600. PostgreSQL16-alpine запускается в lab13 с env-file .db.env и томом lab13_pg:/var/lib/postgresql/data. JCR запускается в той же сети с привязкой var:/var/opt/jfrog/artifactory, лимитом памяти3ГБ и swap4ГБ. Используйте официальный образ releases-docker.jfrog.io/jfrog/artifactory-jcr:7.161.15 и указанные выше loopback-порты.

JVM: `-Xms256m -Xmx768m -XX:ActiveProcessorCount=1 -XX:UseAVX=0 -XX:TieredStopAtLevel=1`. Последние два параметра применены после soft lockup VirtualBox/Hyper-V в C2 CompilerThread. Это обход на данном учебном компьютере, а не доказанное устранение причины ошибки гипервизора.

В system.yaml явно задан `jfconnect.enabled: false`: иначе свободная редакция обращалась к отсутствующему JFConnect, а UI оставался на индикаторе загрузки. Аналогичная проблема описана в https://github.com/jfrog/charts/issues/2233. Это настройка отсутствующего компонента свободной редакции; коммерческие возможности не включались.

Первичная инициализация на одном vCPU занимает несколько минут. Проверяйте `curl http://127.0.0.1:18081/artifactory/api/system/ping` до ответа OK. Ожидаемые временные 503 при запуске не означают готовность реестра.

## Репозитории и доступ

В этой сборке JCR REST-чтение списка доступно, а REST-создание репозитория возвращает сообщение Pro-only. Поэтому репозитории создаются штатным веб-интерфейсом: Docker Local docker-local, Docker Remote docker-remote с URL https://registry-1.docker.io/, Docker Virtual docker, объединяющий первые два, default deployment repository docker-local.

Пароль администратора заменён; значения находятся только в частном файле .secrets.json на VM. Скрипт configure13.py читает его и выполняет Docker login через stdin, с отдельным каталогом .docker-auth. Не публикуйте эти файлы и не вставляйте их в отчёт.

## Проверка артефакта

После создания репозиториев и подготовки закрытого доступа:

```sh
python3 /home/devops/labs13-16/configure13.py
bash /home/devops/labs13-16/verify13.sh
python3 /home/devops/labs13-16/summary13.py
```

Dockerfile строит собственный образ на Alpine, полученном через remote. Push направляется в docker-local, pull выполняется через docker. Проверка сравнивает image ID двух ссылок и запускает контейнер, печатающий имя, группу и версию артефакта. Пароли в вывод не попадают.

Перезапуск контейнера не удаляет данные: конфигурация и filestore находятся в bind mount var, PostgreSQL — в именованном томе. Удаление этих хранилищ уничтожит данные стенда; оно не требуется для демонстрации.

Источники: https://docs.jfrog.com/artifactory/docs/get-started-jfrog-container-registry и https://docs.jfrog.com/artifactory/docs/docker-repositories

В Docker daemon.json добавлен только insecure-registry 127.0.0.1:15000. Прямой endpoint Router18082 отвечал на TLS-пробу ошибкой unrecognized name, и Docker не переходил к HTTP. Локальный HTTP reverse proxy устранил эту проблему. Для применения настройки потребовался restart Docker; live-restore сохранил время запуска контейнера JCR. Nginx-порт не опубликован на внешних интерфейсах.

Проверка push/pull прошла. Digest student-demo:1.0: sha256:4c4361f6c4e4922f31deb80161d08acab95313dd5edef7accbb489c1a559c192. Виртуальная и локальная ссылки совпали; контейнер вывел ФИО, группу и версию1.0. Анонимный запрос manifest получил401. Кэш remote содержит list.manifest.json для library/alpine/3.21.
