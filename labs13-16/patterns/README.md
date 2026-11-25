# Практическая работа 16

Терешин Артем Дмитриевич, ЭФБО-14-24.

Локальные детерминированные модели Retry, Circuit Breaker и Cache Aside из Azure Architecture Center. Это не подключение к Azure. Сеть, источник данных и время моделируются; ожидание по умолчанию не блокирует выполнение. Модель Circuit Breaker последовательная, без потокобезопасности и распределённой координации.

```sh
python3 patterns.py retry
python3 patterns.py limit
python3 patterns.py breaker
python3 patterns.py reopen
python3 patterns.py cache
python3 patterns.py stale
python3 patterns.py test
```

Все шесть тестов прошли на Ubuntu. Проверены ограничение попыток, отказ без повторов при постоянной ошибке, запрет обращений к открытой цепи, успешная и неудачная проба, TTL и инвалидация. В производственной реализации нужны реальное время, jitter, идемпотентность, ограничения памяти, согласованность кэша и конкурентный доступ.

Источник: https://learn.microsoft.com/en-us/azure/architecture/patterns/
