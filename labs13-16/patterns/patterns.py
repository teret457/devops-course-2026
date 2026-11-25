"""Учебные модели Retry, Circuit Breaker и Cache-Aside без облачных расходов."""
import argparse
import unittest

class TransientError(Exception):
    """Временный отказ зависимости."""

def retry(operation, attempts=3, delays=(1, 2), sleep=lambda _: None):
    """Повторяет только временные ошибки с ограничением числа попыток."""
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except TransientError:
            if attempt == attempts:
                raise
            sleep(delays[min(attempt - 1, len(delays) - 1)])

class CircuitOpen(Exception):
    """Автомат разомкнут, реальный вызов запрещён."""

class CircuitBreaker:
    """Последовательная учебная модель; не потокобезопасный production-компонент."""
    def __init__(self, clock, threshold=2, cooldown=5):
        self.clock, self.threshold, self.cooldown = clock, threshold, cooldown
        self.state, self.failures, self.opened = "CLOSED", 0, None
    def call(self, operation):
        if self.state == "OPEN":
            if self.clock() - self.opened < self.cooldown:
                raise CircuitOpen()
            self.state = "HALF_OPEN"
        try:
            result = operation()
        except TransientError:
            self.failures += 1
            if self.state == "HALF_OPEN" or self.failures >= self.threshold:
                self.state, self.opened = "OPEN", self.clock()
            raise
        self.state, self.failures = "CLOSED", 0
        return result

class CacheAside:
    """Кэш с TTL, загрузкой по требованию и явным сбросом при записи."""
    def __init__(self, store, clock, ttl=10):
        self.store, self.clock, self.ttl = store, clock, ttl
        self.cache, self.reads = {}, 0
    def get(self, key):
        item = self.cache.get(key)
        if item and item[1] > self.clock():
            return item[0], "HIT"
        self.reads += 1
        value = self.store[key]
        self.cache[key] = (value, self.clock() + self.ttl)
        return value, "MISS"
    def update(self, key, value):
        self.store[key] = value
        self.cache.pop(key, None)

def demo(name):
    print("Терешин Артем Дмитриевич | ЭФБО-14-24 | ПР16", name)
    print("Локальная детерминированная модель, без Azure. Время ожидания моделируется.")
    if name == "retry":
        calls, delays = [], []
        def flaky():
            calls.append(len(calls) + 1)
            print("Вызов зависимости", len(calls))
            if len(calls) < 3:
                raise TransientError("503")
            return "OK"
        print("Результат", retry(flaky, sleep=delays.append))
        print("Паузы backoff", delays, "Попыток", len(calls))
        assert calls == [1, 2, 3] and delays == [1, 2]
    elif name == "limit":
        calls = []
        def down():
            calls.append(1)
            raise TransientError("503")
        try:
            retry(down)
        except TransientError:
            print("Лимит достигнут; ошибка передана вызывающему коду, попыток", len(calls))
        assert len(calls) == 3
    elif name in ("breaker", "reopen"):
        now = [0]
        cb = CircuitBreaker(lambda: now[0])
        calls = []
        def down():
            calls.append(1)
            raise TransientError()
        for _ in range(2):
            try:
                cb.call(down)
            except TransientError:
                print("Ошибка; состояние", cb.state)
        try:
            cb.call(down)
        except CircuitOpen:
            print("Быстрый отказ OPEN, новых вызовов нет:", len(calls))
        assert len(calls) == 2
        now[0] = 6
        if name == "reopen":
            try:
                cb.call(down)
            except TransientError:
                print("Пробный вызов HALF_OPEN неуспешен; состояние", cb.state)
            assert cb.state == "OPEN"
        else:
            print("Пробный вызов после cooldown:", cb.call(lambda: "OK"), cb.state)
            assert cb.state == "CLOSED"
    elif name in ("cache", "stale"):
        now = [0]
        store = {"price": 100}
        cache = CacheAside(store, lambda: now[0])
        print("Первое чтение", cache.get("price"))
        print("Повторное чтение", cache.get("price"), "Чтений хранилища", cache.reads)
        assert cache.reads == 1
        if name == "stale":
            store["price"] = 120
            print("Внешняя запись без invalidation: старое значение", cache.get("price"))
            now[0] = 11
            print("После TTL", cache.get("price"))
            assert cache.get("price")[0] == 120
        else:
            cache.update("price", 130)
            print("Запись со сбросом кэша", cache.get("price"))
            assert cache.get("price")[0] == 130

class PatternTests(unittest.TestCase):
    def test_transient_and_backoff(self):
        calls, delays = [], []
        def operation():
            calls.append(1)
            if len(calls) < 3:
                raise TransientError()
            return 7
        self.assertEqual(retry(operation, sleep=delays.append), 7)
        self.assertEqual(delays, [1, 2])
    def test_non_transient_not_retried(self):
        calls = []
        def operation():
            calls.append(1)
            raise ValueError("bad input")
        with self.assertRaises(ValueError):
            retry(operation)
        self.assertEqual(len(calls), 1)
    def test_retry_exhaustion(self):
        with self.assertRaises(TransientError):
            retry(lambda: (_ for _ in ()).throw(TransientError()))
    def test_circuit_blocks_and_recovers(self):
        clock = [0]
        cb = CircuitBreaker(lambda: clock[0])
        for _ in range(2):
            with self.assertRaises(TransientError):
                cb.call(lambda: (_ for _ in ()).throw(TransientError()))
        with self.assertRaises(CircuitOpen):
            cb.call(lambda: "unused")
        clock[0] = 6
        self.assertEqual(cb.call(lambda: 42), 42)
        self.assertEqual(cb.state, "CLOSED")
    def test_half_open_failure(self):
        clock = [0]
        cb = CircuitBreaker(lambda: clock[0], threshold=1)
        for tick in [0, 6]:
            clock[0] = tick
            with self.assertRaises(TransientError):
                cb.call(lambda: (_ for _ in ()).throw(TransientError()))
            self.assertEqual(cb.state, "OPEN")
    def test_cache_ttl_and_invalidation(self):
        clock = [0]
        store = {"k": 1}
        c = CacheAside(store, lambda: clock[0])
        self.assertEqual(c.get("k"), (1, "MISS"))
        self.assertEqual(c.get("k"), (1, "HIT"))
        store["k"] = 2
        self.assertEqual(c.get("k")[0], 1)
        clock[0] = 11
        self.assertEqual(c.get("k"), (2, "MISS"))
        c.update("k", 3)
        self.assertEqual(c.get("k"), (3, "MISS"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", choices=["retry", "limit", "breaker", "reopen", "cache", "stale", "test"])
    args = parser.parse_args()
    if args.scenario == "test":
        unittest.main(argv=["patterns"], verbosity=2)
    else:
        demo(args.scenario)
