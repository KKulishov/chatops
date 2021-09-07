from os import path, getenv
import re
from errbot import BotPlugin, arg_botcmd, botcmd, re_botcmd, webhook
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import paramiko
from mylib import get_id_vm, stop_vm, start_vm, list_vm_build, update_vm, protected_branches, unprotect_branches

current_dir = path.dirname(path.realpath(__file__))

password_ssh = getenv("CI_support_password")
login_ssh = getenv("CI_support_login")
instace_remote = getenv("CI_support_server")

folderId = getenv("CI_folderId")

configuration = client.Configuration()
configuration.api_key_prefix['authorization'] = 'Bearer'
configuration.api_key['authorization'] = getenv("KUBER_TOKEN_VIEWER")
configuration.host = getenv("K8S_API_URL_PROD")
configuration.ssl_ca_cert = current_dir + "/ca.crt"

with client.ApiClient(configuration) as api_client:
    api_instance = client.CoreV1Api(api_client)
namespace = 'None'
follow = True
insecure_skip_tls_verify_backend = False
previous = True
since_seconds = 56
tail_lines = 56
timestamps = True

FRONT_RE = re.compile(r"^pre-migrate-db-(.*)")

def get_migration_pod_name(namespace: str):
    try:
        api_response = api_instance.list_namespaced_pod(namespace=namespace)
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)
    for pod in api_response.items:
        if matcher := re.search(FRONT_RE, pod.metadata.name):
            return matcher.group()


class Rights(BotPlugin):

    @arg_botcmd("--namespace", dest="namespace", type=str)
    def logs_migrated(self, _, namespace):
        """
        Выводит логи миграции при CI/CD деплои
        :param _:
        :param namespace: указывает namespace в kubernetes
        :return: возвращает лог
        """
        pod_name = get_migration_pod_name(namespace)
        container = 'pre-migrate-db'
        try:
            api_response = api_instance.read_namespaced_pod_log(name=pod_name, namespace=namespace, container=container)
            return api_response
        except ApiException as e:
            print("Exception when calling CoreV1Api->read_namespaced_pod_log: %s\n" % e)

    @arg_botcmd("--name_vm", dest="name_vm", type=str)
    def stop_vm(self, _, name_vm):
        id_vm = get_id_vm(name_vm)
        result = stop_vm(id_vm)
        if result['done'] is False or True:
            result = f"VM is stopping {name_vm}"
        else:
            result = result['error']
        return result

    @arg_botcmd("--name_vm", dest="name_vm", type=str)
    def start_vm(self, _, name_vm):
        id_vm = get_id_vm(name_vm)
        result = start_vm(id_vm)
        if result['done'] is False or True:
            result = f"VM is running {name_vm}"
        else:
            result = result['error']
        return result

    @arg_botcmd("--name_vm", dest="name_vm", type=str)
    def status_vm(self, _, name_vm):
        # depricated, можно  использовать list_build_vm
        with paramiko.SSHClient() as ssh_client:
            ssh_client.load_system_host_keys()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            ssh_client.connect(instace_remote, 22, login_ssh, password=password_ssh)
            stdin, stdout, stderr = ssh_client.exec_command(
                "/home/chatops/yandex-cloud/bin/yc compute instance get " + name_vm + " | grep status")
            status = stdout.read().decode()
        return f"VM {name_vm} {status}"

    @botcmd
    def tryme(self, msg, args):
        return "It *works* !"

    @arg_botcmd("--name_vm", dest="name_vm", type=str)
    @arg_botcmd("--core", dest="core", type=str)
    @arg_botcmd("--mem", dest="mem", type=str)
    def upgrade_vm(self, _, name_vm, core, mem):
        result = update_vm(name_vm, core, mem)
        yield result

    @botcmd
    def list_build_vm(self, msg, args):
        """
        Возрвращает список vm которые задействованы в сборки проекта
        :return:
        """
        matcher, status_vm, status_vm, core_vm, memory_vm = list_vm_build()
        yield f"Имя: {matcher}, Статус: {status_vm}, Ядра: {core_vm}, ОЗУ: {memory_vm} ГБ"

    @arg_botcmd("--name", type=str)
    def protected_gitlab(self, _, name):
        protected_branches(name)
        return f"Gitlab ветка {name} защищена"

    @arg_botcmd("--name", type=str)
    def unprotect_gitlab(self, _, name):
        unprotect_branches(name)
        return f"Gitlab ветка {name} защита снята"

    def callback_message(self, message) -> None:
        if any(trigger in message.body.lower() for trigger in ["helps", "man"]):
            self.send(message.to,
                      "You can use command: \n"
                      "В примере использую имя buildfront, но это может быть любая vm \n"
                      "/list build vm                                -- Список воркеров сборки их состояния и мощности\n"
                      "/stop vm --name_vm buildfront                 -- Запустить виртуальную машину \n"
                      "/start vm --name_vm buildfront                -- Запустить виртуальную машину \n"
                      "/upgrade vm --name_vm buildfront --core 4 --mem 8   -- Upgrde ВМ на 4 ядра и ОЗУ 8 ГБ \n"
                      "/status vm --name_vm buildfront               -- В каком состоянии сейчас виртуальную машина (Включена или выключена) \n"
                      "/logs_migrated --namespace work               -- Логи миграции БД, перед деплоем, имя namespace менеяться\n"
                      "/protected_gitlab --name work                 -- Защитить ветку от изменений\n"
                      "/unprotect_gitlab --name work                 -- Снять защиту с  ветки\n"
                      )
        elif any(trigger in message.body.lower() for trigger in ["ты красавчик", "ты молодец"]):
            self.send(message.to,
                      "Я знаю )")
