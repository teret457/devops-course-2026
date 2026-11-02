# Конфигурация виртуальной машины devops-vm

Студент: Терешин Артем Дмитриевич, ЭФБО-14-24.

## 1. Параметры машины
Ubuntu Server 24.04 LTS без графической оболочки. VirtualBox 7.0.20. Диск VDI 25 ГБ динамический, 2 ядра, 2048 МБ RAM после установки. Во время установки временно выделено 4096 МБ.

## 2. Сетевые интерфейсы
Адаптер 1 NAT: enp0s3, 10.0.2.15/24, доступ в Интернет. Адаптер 2 Host-only: enp0s8, 192.168.56.101/24, связь с хостом 192.168.56.1. DHCP Host-only находится в сети 192.168.56.0/24.

## 3. Правило проброса портов
После установки: 127.0.0.1:2222 хоста -> 22 гостя. После hardening: 127.0.0.1:2222 -> 2222 гостя. Имя правила ssh, протокол TCP.

## 4. Учётные записи
student создан установщиком, входит в sudo. devops создан командой sudo useradd -m -s /bin/bash devops, включён в sudo командой sudo usermod -aG sudo devops. Пароль sudo хранится отдельно от репозитория. Ключ клиента ~/.ssh/devops_vm; его закрытая часть не передаётся на сервер. На сервер переносится только devops_vm.pub в /home/devops/.ssh/authorized_keys. Каталог .ssh имеет права 700, authorized_keys 600, владелец devops.

Клиентский псевдоним:
```sshconfig
Host devops
    HostName 127.0.0.1
    User devops
    Port 2222
    IdentityFile ~/.ssh/devops_vm
    IdentitiesOnly yes
```

## 5. Служба SSH
Эталон: /etc/ssh/sshd_config.backup. Изменения: /etc/ssh/sshd_config.d/99-hardening.conf.
```text
Port 2222
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
MaxAuthTries 3
LoginGraceTime 30
AllowUsers devops
X11Forwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
```
Конфликтующие ранние PasswordAuthentication yes в sshd_config.d нужно закомментировать. Контроль: sudo sshd -t; sudo sshd -T. Для Ubuntu с socket activation: sudo systemctl disable --now ssh.socket; sudo systemctl enable ssh.service; sudo systemctl restart ssh.service. Фактический порт: sudo ss -tlnp | grep sshd. Первую сессию держать открытой до проверки нового подключения после изменения проброса VirtualBox.

## 6. Правила межсетевого экрана
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 2222/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw delete allow 2222/tcp
sudo ufw limit 2222/tcp
sudo ufw logging medium
sudo ufw status verbose
```
Сначала разрешается управляющий порт, затем включается экран. В hosts Windows и WSL: 192.168.56.101 devops.local. На сервере hostname devops-vm, строка /etc/hosts: 127.0.1.1 devops-vm.devops.local devops-vm. Аудит: scripts/audit.sh.

## 7. Снимки состояния
01-clean-install: установленная Ubuntu до создания devops. 02-keys-configured: пользователь и ключи. 03-ssh-hardened: защищённый SSH, нестандартный порт. 04-nginx-https: Nginx с HTTPS. 05-docker-compose: приложение и PostgreSQL. 06-before-kr2: готовый стенд перед КР. 07-kr2: итог КР. Снимки создаются по достижении соответствующего этапа.

## 8. Веб-сервер
Установка: sudo apt update && sudo apt install nginx rsync openssl. systemctl enable --now nginx. Ресурс: /etc/nginx/sites-available/devops-site, ссылка в /etc/nginx/sites-enabled/. Стандартная ссылка default отключена. Каталог /var/www/devops-site принадлежит devops:devops, права каталогов 755, файлов 644; www-data читает без записи.

Сертификат /etc/ssl/certs/devops.crt (644), ключ /etc/ssl/private/devops.key (root:root, 600). Создание на 365 дней:
```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/devops.key -out /etc/ssl/certs/devops.crt -subj '/CN=devops.local' -addext 'subjectAltName=DNS:devops.local'
sudo chmod 600 /etc/ssl/private/devops.key
```
Сертификат копируется на хост в ~/devops.crt; закрытый ключ остаётся на сервере. HTTP на 80 возвращает return 301 https://$host$request_uri. HTTPS на 443 использует этот сертификат и TLSv1.2/TLSv1.3, root /var/www/devops-site, index index.html. Настроены error_page 404 /404.html и internal location = /404.html. Журналы: /var/log/nginx/devops-site.access.log и devops-site.error.log.

Перед каждым применением: sudo nginx -t && sudo systemctl reload nginx. Доставка: scripts/deploy.sh [--dry-run]. Сценарий проверяет чистоту Git и index.html, вызывает rsync --delete --chmod=D755,F644 с BatchMode=yes, затем curl --fail --cacert ~/devops.crt. Аудит включает активность Nginx, синтаксис, остаточный срок сертификата 30 дней, отсутствие world-writable файлов и права ключа.

## 9. Контейнеризация
Docker Engine 29.9.2 установлен из https://download.docker.com/linux/ubuntu (suite noble, stable), пакеты docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin. Compose 5.7.0. Пользователь devops включён в docker; членство даёт фактические права root.

Проект /home/devops/app содержит Dockerfile, app.py, requirements.txt, .dockerignore и docker-compose.yml. Серверный .env принадлежит devops, права 600; пароль PostgreSQL создаётся openssl rand -hex 16 и не копируется на хост. Сеть app_backend, том app_db_data. Приложение доступно только на 127.0.0.1:5000, PostgreSQL не публикуется. depends_on ожидает healthy базы. Политики перезапуска unless-stopped.

Nginx location /app/ использует proxy_pass http://127.0.0.1:5000/ и передаёт Host, X-Real-IP, X-Forwarded-For и X-Forwarded-Proto. Конфигурация сохранена в configs/devops-site.conf. Контроль: docker compose ps; docker compose exec -T app id; docker compose exec -T app getent hosts db; ss -tlnp; scripts/audit.sh.

В режиме VirtualBox через Hyper-V наблюдались сообщения kernel soft lockup. Для завершения ресурсоёмких операций CPU 1 временно выведен offline через /sys/devices/system/cpu/cpu1/online. В параметрах VM остаются 2 vCPU; при перезагрузке ядро снова активируется. Обратная операция: echo 1 | sudo tee /sys/devices/system/cpu/cpu1/online. Этот обход не меняет настройки защиты Windows.

## 10. Контрольная работа 2
Вариант 2, номер 22: notes.devops.local, приложение 8002. Проект /home/devops/kr2, образ kr2-app:1.0, Redis redis:7-alpine, сеть kr2_backend, том kr2_redis_data. Порт приложения публикуется только на 127.0.0.1:8002, Redis не публикуется. Пароль REDIS_PASSWORD создаётся на сервере openssl rand -hex 16, файл /home/devops/kr2/.env имеет права 600 и не перезаписывается rsync. При доставке исключаются .env и .git.

Nginx: /etc/nginx/sites-available/kr2 и ссылка sites-enabled/kr2, HTTP 301, HTTPS проксирует на 127.0.0.1:8002. Передаются Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto. Сертификат /etc/ssl/certs/kr2.crt имеет SAN notes.devops.local и срок 365 дней, ключ /etc/ssl/private/kr2.key — root:root 600. На хост копируется только открытый сертификат. Конфигурация сохранена в репозитории КР как nginx/kr2.conf.

Аудит расширен разделом [6]: healthy Redis, точная loopback публикация 8002, .env 600, сертификат не истекает 30 дней и сайт активирован. Правила UFW до и после КР совпадают. ПР 6 и 7 продолжают работать. Снимки 06-before-kr2 и 07-kr2 созданы. Ветка kr2/variant-2 оставлена открытым Pull Request без слияния до защиты.

## 11. Проверка восстановления
Из снимка 01-clean-install создан отдельный связанный клон devops-restore-check. На нём повторены создание devops и ключей, hardening SSH и настройка UFW. Аудит этапа 5 прошёл все 6 проверок. Рабочий стенд при проверке не откатывался и не прерывался. После проверки вспомогательный клон выключен.
