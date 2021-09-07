from os import getenv
import json
import re
import time
import requests
import gitlab

ERRBOT_ENV = getenv("ERRBOT_ENV")
folderId = getenv("CI_folderId")
api_yandex_cloud = "https://compute.api.cloud.yandex.net/compute/v1/instances/"
api_yandex_token = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
gitlab_token = getenv("CI_gitlab_token")
gitlab_id = getenv("CI_gitlab_id")

def protected_branches(name: str):
    gl = gitlab.Gitlab("https://gitlab.com", gitlab_token)
    project = gl.projects.get(gitlab_id)
    branch = project.branches.get(name)
    branch.protect(developers_can_push=False, developers_can_merge=False)
    return f"branch {name} protected"

def unprotect_branches(name: str):
    gl = gitlab.Gitlab("https://gitlab.com", gitlab_token)
    project = gl.projects.get(gitlab_id)
    branch = project.branches.get(name)
    branch.unprotect(developers_can_push=False, developers_can_merge=False)
    return f"branch {name} protected"

def get_iam_token():
    """
        Получения IAM token при условии, что запрос идет внутри подсети yandex cloud  и на instance есть сервис аккаунт
        Тут подробнее
        https://cloud.yandex.ru/docs/compute/operations/vm-connect/auth-inside-vm
        :return: Возвращает IAM token для послед. работы с yandex cloud
    """
    if ERRBOT_ENV == "PROD":
        session = requests.Session()
        base_url = api_yandex_token
        headers = {
            "Metadata-Flavor": 'Google'
        }
        try:
            response = session.get(url=base_url, headers=headers, timeout=5)
            test = response.content
            result = json.loads(test)
        except requests.exceptions.ConnectTimeout:
            print("Ресурс недоступен")
        return result['access_token']
    elif ERRBOT_ENV == "DEV":
        CI_IAM_TOKEN = getenv("CI_IAM_TOKEN")
        return CI_IAM_TOKEN
    else:
        print('Переменная ERRBOT_ENV не задана или задано, но она несоотвествует значением PROD или DEV')

def stop_vm(id_vm: str):
    """
    Останавливает VM
    :param id_vm: id vm для каждого он свой
    :return: возвращает стсатус ответа при выполнении
    """
    IAM_TOKEN = get_iam_token()
    session = requests.Session()
    base_url = api_yandex_cloud + id_vm + ":stop"
    headers = {
        "Authorization": 'Bearer ' + IAM_TOKEN
    }
    try:
        response = session.post(url=base_url, headers=headers, timeout=5)
    except requests.exceptions.ConnectTimeout:
        print("Ресуср не доступен")
    result = json.loads(response.content)
    if 'error' in result:
        return result['error']
    else:
        return result

def start_vm(id_vm: str):
    """
    Стартует vm по указаному id
    :param id_vm:
    :return: озвращает стсатус ответа при выполнении
    """
    IAM_TOKEN = get_iam_token()
    session = requests.Session()
    base_url = api_yandex_cloud + id_vm + ":start"
    headers = {
        "Authorization": 'Bearer ' + IAM_TOKEN
    }
    try:
        response = session.post(url=base_url, headers=headers, timeout=5)
    except requests.exceptions.ConnectTimeout:
        print("Ресуср не доступен")
    result = json.loads(response.content)
    if 'error' in result:
        return result['error']
    else:
        return result

def get_id_vm(name_vm: str):
    """
    Получает id vm
    :param name_vm:  Имя vm
    :return: Возвращает id vm , в послед. можно с ним работать
    """
    IAM_TOKEN = get_iam_token()
    session = requests.Session()
    base_url = api_yandex_cloud
    headers = {
        "Authorization": 'Bearer ' + IAM_TOKEN
    }
    query_params = {
        "folderId": folderId
    }
    try:
        response = session.get(url=base_url, params=query_params, headers=headers, timeout=5)
        result = json.loads(response.content)
    except requests.exceptions.ConnectTimeout:
        print("Ресурс недоступен")
    for instances in result['instances']:
        if name_vm == instances['name']:
            id_vm = instances['id']
            return id_vm

def list_vm_build():
    """
    Список vm которые занимаютьс сборкой кода В gitlab/ci runner
    :return: Возвращает имя vm его статус и тех. характеристики
    """
    build_vm = re.compile(r"^build(.*)")  # по хорошему делать метки и по labels делать фильтрацию
    IAM_TOKEN = get_iam_token()
    session = requests.Session()
    base_url = api_yandex_cloud
    headers = {
        "Authorization": 'Bearer ' + IAM_TOKEN
    }
    query_params = {
        "folderId": folderId
    }
    try:
        response = session.get(url=base_url, params=query_params, headers=headers, timeout=5)
        test = response.content
        result = json.loads(test)
    except requests.exceptions.ConnectTimeout:
        print("Ресурс недоступен")
    for instances in result['instances']:
        name_vm = instances['name']
        if 'error' not in instances:
            if matcher := re.search(build_vm, name_vm):
                matcher = matcher.group()
                id_vm = instances['id']
                status_vm = instances['status']
                memory_vm = int(instances['resources']['memory']) / 1024 / 1024 / 1024
                core_vm = instances['resources']['cores']
                list_vm_param = matcher, status_vm, status_vm, core_vm, memory_vm
                #return matcher, status_vm, status_vm, core_vm, memory_vm
                return list_vm_param
        else:
            list_vm_param = instances['error']
            return list_vm_param

def update_vm(name_vm, core, mem):
    """
    Производит обновления vm по заданным характеристикам
    :param name_vm: имя машины
    :param core: кол-во ядер
    :param mem: ОЗУ в ГБ
    :return: Возвращает положительные результат работы или отрицательный
    """
    IAM_TOKEN = get_iam_token()
    session = requests.Session()
    id_vm = get_id_vm(name_vm)
    mem_vm = int(mem) * 1024 * 1024 * 1024
    stop_vm(id_vm)
    print("Please wait 10s, vm stopings")
    time.sleep(10)

    base_url = api_yandex_cloud + id_vm
    headers = {
        "Authorization": 'Bearer ' + IAM_TOKEN
    }
    data_update = {
        "updateMask": "resourcesSpec",
        "resourcesSpec": {
            "memory": mem_vm,
            "cores": core,
            "coreFraction": "100",
        }
    }
    try:
        response = session.patch(url=base_url, headers=headers, json=data_update, timeout=5)
    except requests.exceptions.ConnectTimeout:
        print("Ресурс недоступен")
    result = json.loads(response.content)

    if 'error' in result:
        return result['error']

    if result['done'] is True:
        time.sleep(1)
        start_vm(id_vm)
        result = f"Update {name_vm} done, please wait 10s for when vm up"
    elif result['done'] is False:
        try:
            response = session.patch(url=base_url, headers=headers, json=data_update, timeout=5)
        except requests.exceptions.ConnectTimeout:
            print("Ресурс недоступен")
        start_vm(id_vm)
        result = f"Update {name_vm} done, please wait 10s for when vm up"
    else:
        result = result['error']

    return result

def get_branches():
    gl = gitlab.Gitlab("https://gitlab.com", gitlab_token)
    project = gl.projects.get("27131312")
    branches = project.branches.list()
    return branches
