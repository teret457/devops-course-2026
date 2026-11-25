# Практическая работа 14

Application отслеживает https://github.com/teret457/devops-gitops.git, main, app/. Манифесты Deployment, ConfigMap и Service находятся в этом отдельном репозитории.

```sh
sudo k3s kubectl apply -f application.yaml
sudo k3s kubectl get app lab14 -n argocd
```

Проверены автоматическая синхронизация, версия 1 → 2 с одной → двумя репликами, selfHeal после kubectl scale до четырёх, возврат к версии 1 и одной реплике новым коммитом Git. Обновление и откат прошли через PR1 и PR2 в devops-gitops. Принудительная аннотация refresh ускоряет чтение Git и не меняет желаемое состояние.

K3s v1.34.3+k3s1, Argo CD v3.6.3, Ubuntu24.04, VM6GB/1CPU. Установка K3s без traefik и servicelb; доступ к API и интерфейсам локальный. Kubeconfig, пароль Argo CD и SSH-ключи в Git не хранятся.
