## Проект по взаимодействию с инфраструктурой через chat 

Подробнее в статье на [habre](https://habr.com/ru/companies/southbridge/articles/577662/)

### Установка зависимостей 

```
pip3 install errbot errbot[telegram] paramiko kubernetes requests python-gitlab
```

Офф. доки по 
[errbot](https://errbot.readthedocs.io/en/latest/)
[kubernetes](https://github.com/kubernetes-client/python)
[python-gitlab](https://python-gitlab.readthedocs.io/en/stable/)

#### Перед запускам проекта, необходима экспортировать след. переменные 

Есть два значения данной переменной PROD и DEV, если указать DEV то переодделиться параметры запуска ПО, errbot запуститься в text режиме 
```
export ERRBOT_ENV="DEV"
```

для взаимодействия с yandex api (необязательно), нужно импортировать уникальный id каталаог и iam token c правами взаимодействия computer instance 
```
export CI_folderId="XXXXXXXXXXXX"
export CI_IAM_TOKEN="XXXXXXXXXXXXXXX"
```

для взаимодействия с gitlab, нужен токен и id проекта в gitlab (необязательно)
```
export CI_gitlab_token="XXXXXXXXXXXXxx"
export CI_gitlab_id="XXXXXXXXXXXXXXX"
```

для взаимодействия с kubernetes (необязательно). 
```
export K8S_API_URL_PROD="ip api server"
export KUBER_TOKEN_VIEWER="token kubernetes" 
```
!!! Описать создания учетки 
тут могу отметить что данному аккаунту и предоставляем заранее созданную роль view, который имеет права только на просмотр, но все зависит от Ваших требований и реализаций.  
```
kubectl create serviceaccount chatbot
kubectl create clusterrolebinding chatbot-cluster-view --clusterrole=view --serviceaccount=default:chatbot
kubectl get secret chatbot-token-xj54b -o jsonpath="{['data']['token']}" | base64 -d
kubectl get secret chatbot-token-xj54b -o jsonpath="{['data']['ca\.crt']}" | base64 -d
```


так же нужен сертификат и положить его нужно назвать ca.crt и положить plugins/err-prod/ca.crt

### и так после запуска приложения , вызовом
```
errbot
```

Можно получить логи миграции БД (если настроено взамодействия с kubernetes)
```
/logs_migrated --namespace work
```

Можно понять сколько runner участвуют в сборки проекта и их тех. характ.
```
/list build vm
```
Можно стартовать vm или останавливать
```
/start vm --name_vm name_vm
/stop vm --name_vm name_vm
```

Так же возможно и производить модификацию vm над тек. по увелечению мощностей, что эквивалентно 4 ядрам и 8 Гб ОЗУ 
```
/upgrade vm --name_vm name_vm --core 4 --mem 8
```

Можно установить защиту на ветку проекта от изменения, где --name это имя ветки 
```
/protected_gitlab --name work  
```
или снять защиту
```
/unprotect_gitlab --name work 
```


Для работы telegram нужен api token bota
```
export BOT_TOKEN="token telegram bota"
```

!!! сменить свой id admin в config.py 
```
BOT_ADMINS
```
