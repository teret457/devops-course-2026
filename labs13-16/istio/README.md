# Практическая работа 15

Терешин Артем Дмитриевич, ЭФБО-14-24.

Исходный Bookinfo: официальные samples релиза Istio 1.32.0, авторство Istio Authors сохранено. Архив скачан с GitHub Istio, SHA256 проверен. Требуется работающий Kubernetes; в опыте K3s v1.34.3+k3s1 на Ubuntu 24.04.

`sudo bash install.sh` использует предварительно распакованный `~/labs13-16/istio-1.32.0`; при sudo передайте ISTIO_HOME явно. Скрипт повторяет итоговую конфигурацию эксперимента; установка уже выполнена. Для последовательного показа v1 и v3 применяйте соответствующие файлы samples/bookinfo/networking/virtual-service-all-v1.yaml и virtual-service-reviews-v3.yaml. После all-v1 удалите ненужный VirtualService productpage, чтобы его правило subset не конфликтовало с входным bookinfo.

`traffic.py` запускается внутри контейнера productpage, где установлен requests. Сначала скопируйте его через kubectl cp, затем:

```sh
sudo k3s kubectl exec -n lab15 deploy/productpage-v1 -c productpage -- python3 /tmp/traffic.py 100
sudo k3s kubectl port-forward -n istio-system svc/istio-ingressgateway 18090:80 --address 127.0.0.1
```

В браузере VM: http://127.0.0.1:18090/productpage. На Windows используйте SSH-туннель, не открывайте интерфейс на всех адресах.

Проверено: 30/30 v1, 30/30 v3, правило 50/50 дало 48/52 на 100 запросах. В PERMISSIVE outsider без Envoy получил details, в STRICT получил reset и exit1. Внутри mesh десять запросов успешны. Analyze после удаления отсутствующих subsets ratings проходит.

Профиль demo и сниженные ресурсы предназначены для локальной демонстрации. Высокая доступность не реализована. После перезагрузки kubectl port-forward запускается заново.
