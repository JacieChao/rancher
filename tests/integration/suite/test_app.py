from .common import random_str
from .test_catalog import wait_for_template_to_be_created
import pytest
import time


def test_app_mysql(admin_pc, admin_mc):
    client = admin_pc.client
    name = random_str()

    ns = admin_pc.cluster.client.create_namespace(name=random_str(),
                                                  projectId=admin_pc.
                                                  project.id)
    wait_for_template_to_be_created(admin_mc.client, "library")
    answers = {
        "defaultImage": "true",
        "image": "mysql",
        "imageTag": "5.7.14",
        "mysqlDatabase": "admin",
        "mysqlPassword": "",
        "mysqlUser": "admin",
        "persistence.enabled": "false",
        "persistence.size": "8Gi",
        "persistence.storageClass": "",
        "service.nodePort": "",
        "service.port": "3306",
        "service.type": "ClusterIP"
    }
    client.create_app(
        name=name,
        externalId="catalog://?catalog=library&template=mysql&version=0.3.7&"
                   "namespace=cattle-global-data",
        targetNamespace=ns.name,
        projectId=admin_pc.project.id,
        answers=answers
    )
    wait_for_workload(client, ns.name, count=1)


def test_app_wordpress(admin_pc, admin_mc):
    client = admin_pc.client
    name = random_str()

    ns = admin_pc.cluster.client.create_namespace(name=random_str(),
                                                  projectId=admin_pc.
                                                  project.id)
    wait_for_template_to_be_created(admin_mc.client, "library")
    answers = {
        "defaultImage": "true",
        "externalDatabase.database": "",
        "externalDatabase.host": "",
        "externalDatabase.password": "",
        "externalDatabase.port": "3306",
        "externalDatabase.user": "",
        "image.repository": "bitnami/wordpress",
        "image.tag": "4.9.4",
        "ingress.enabled": "true",
        "ingress.hosts[0].name": "xip.io",
        "mariadb.enabled": "true",
        "mariadb.image.repository": "bitnami/mariadb",
        "mariadb.image.tag": "10.1.32",
        "mariadb.mariadbDatabase": "wordpress",
        "mariadb.mariadbPassword": "",
        "mariadb.mariadbUser": "wordpress",
        "mariadb.persistence.enabled": "false",
        "mariadb.persistence.size": "8Gi",
        "mariadb.persistence.storageClass": "",
        "nodePorts.http": "",
        "nodePorts.https": "",
        "persistence.enabled": "false",
        "persistence.size": "10Gi",
        "persistence.storageClass": "",
        "serviceType": "NodePort",
        "wordpressEmail": "user@example.com",
        "wordpressPassword": "",
        "wordpressUsername": "user"
    }
    external_id = "catalog://?catalog=library&template=wordpress" \
                  "&version=1.0.5&namespace=cattle-global-data"
    client.create_app(
        name=name,
        externalId=external_id,
        targetNamespace=ns.name,
        projectId=admin_pc.project.id,
        answers=answers
    )
    wait_for_workload(client, ns.name, count=2)


@pytest.mark.skip(reason="istio disabled")
def test_app_istio(admin_cc, admin_pc, admin_mc):
    client = admin_pc.client
    name = "rancher-istio"
    url = "	https://github.com/guangbochen/system-charts.git"
    external_id = "catalog://?catalog=system-library" \
                  "&template=rancher-istio&version=1.1.5"

    ns = admin_pc.cluster.client.create_namespace(name="istio-system",
                                                  projectId=admin_pc.
                                                  project.id)
    admin_mc.client.create_catalog(name="system-library",
                                   branch="istio",
                                   url=url,
                                   )
    wait_for_template_to_be_created(admin_mc.client, "system-library")

    answers = {
        "certmanager.enabled": "false",
        "enableCRDs": "true",
        "galley.enabled": "true",
        "gateways.enabled": "false",
        "gateways.istio-ingressgateway.type": "NodePort",
        "grafana.enabled": "true",
        "grafana.persistence.enabled": "false",
        "istio_cni.enabled": "false",
        "istiocoredns.enabled": "false",
        "kiali.enabled": "true",
        "mixer.enabled": "true",
        "mixer.policy.enabled": "false",
        "mixer.telemetry.resources.limits.cpu": "4800m",
        "mixer.telemetry.resources.limits.memory": "4048Mi",
        "mixer.telemetry.resources.requests.cpu": "1000m",
        "mixer.telemetry.resources.requests.memory": "1024Mi",
        "mtls.enabled": "false",
        "nodeagent.enabled": "false",
        "pilot.enabled": "true",
        "pilot.resources.limits.cpu": "1000m",
        "pilot.resources.limits.memory": "4096Mi",
        "pilot.resources.requests.cpu": "500m",
        "pilot.resources.requests.memory": "2048Mi",
        "pilot.traceSampling": "1",
        "prometheus.enabled": "true",
        "prometheus.resources.limits.cpu": "1000m",
        "prometheus.resources.limits.memory": "1000Mi",
        "prometheus.resources.requests.cpu": "750m",
        "prometheus.resources.requests.memory": "750Mi",
        "prometheus.retention": "6h",
        "security.enabled": "true",
        "sidecarInjectorWebhook.enabled": "true",
        "tracing.enabled": "true"
    }

    client.create_app(
        name=name,
        externalId=external_id,
        targetNamespace=ns.name,
        projectId=admin_pc.project.id,
        answers=answers
    )
    wait_for_monitor_metric(admin_cc, admin_mc)


def test_prehook_chart(admin_pc, admin_mc):
    client = admin_pc.client
    name = random_str()

    ns = admin_pc.cluster.client.create_namespace(name=random_str(),
                                                  projectId=admin_pc.
                                                  project.id)
    url = "https://github.com/StrongMonkey/charts-1.git"
    catalog = admin_mc.client.create_catalog(name=random_str(),
                                             branch="test",
                                             url=url,
                                             )
    wait_for_template_to_be_created(admin_mc.client, catalog.name)
    external_id = "catalog://?catalog=" + \
                  catalog.name + "&template=busybox&version=0.0.2" \
                                 "&namespace=cattle-global-data"
    client.create_app(
        name=name,
        externalId=external_id,
        targetNamespace=ns.name,
        projectId=admin_pc.project.id,
    )
    # it will be only one workload(job), because the deployment has to
    # wait for job to be finished, and it will never finish because we
    # can't create real container
    wait_for_workload(client, ns.name, count=1)
    jobs = client.list_job(namespaceId=ns.id)
    assert len(jobs) == 1


def test_app_namespace_annotation(admin_pc, admin_mc):
    client = admin_pc.client
    ns = admin_pc.cluster.client.create_namespace(name=random_str(),
                                                  projectId=admin_pc.
                                                  project.id)
    wait_for_template_to_be_created(admin_mc.client, "library")
    app1 = client.create_app(
        name=random_str(),
        externalId="catalog://?catalog=library&template=mysql&version=0.3.7"
                   "&namespace=cattle-global-data",
        targetNamespace=ns.name,
        projectId=admin_pc.project.id,
    )
    wait_for_workload(client, ns.name, count=1)

    external_id = "catalog://?catalog=library&template=wordpress" \
                  "&version=1.0.5&namespace=cattle-global-data"
    app2 = client.create_app(
        name=random_str(),
        externalId=external_id,
        targetNamespace=ns.name,
        projectId=admin_pc.project.id,
    )
    wait_for_workload(client, ns.name, count=3)
    ns = admin_pc.cluster.client.reload(ns)
    ns = wait_for_app_annotation(admin_pc, ns, app1.name)
    ns = wait_for_app_annotation(admin_pc, ns, app2.name)
    client.delete(app1)
    wait_for_app_to_be_deleted(client, app1)

    ns = admin_pc.cluster.client.reload(ns)
    assert app1.name not in ns.annotations['cattle.io/appIds']
    assert app2.name in ns.annotations['cattle.io/appIds']

    client.delete(app2)
    wait_for_app_to_be_deleted(client, app2)
    ns = admin_pc.cluster.client.reload(ns)
    assert 'cattle.io/appIds' not in ns.annotations


def wait_for_app_annotation(admin_pc, ns, app_name, timeout=60):
    start = time.time()
    interval = 0.5
    ns = admin_pc.cluster.client.reload(ns)
    while app_name not in ns.annotations['cattle.io/appIds']:
        if time.time() - start > timeout:
            print(ns.annotations)
            raise Exception('Timeout waiting for app annotation')
        time.sleep(interval)
        interval *= 2
        ns = admin_pc.cluster.client.reload(ns)
    return ns


def test_app_custom_values_file(admin_pc, admin_mc):
    client = admin_pc.client
    ns = admin_pc.cluster.client.create_namespace(name=random_str(),
                                                  projectId=admin_pc.
                                                  project.id)
    wait_for_template_to_be_created(admin_mc.client, "library")
    values_yaml = "replicaCount: 2\r\nimage:\r\n  " \
                  "repository: registry\r\n  tag: 2.7"
    answers = {
        "image.tag": "2.6"
    }
    app = client.create_app(
        name=random_str(),
        externalId="catalog://?catalog=library&template=docker-registry"
                   "&version=1.6.1&namespace=cattle-global-data",
        targetNamespace=ns.name,
        projectId=admin_pc.project.id,
        valuesYaml=values_yaml,
        answers=answers
    )
    workloads = wait_for_workload(client, ns.name, count=1)
    workloads = wait_for_replicas(client, ns.name, count=2)
    print(workloads)
    assert workloads.data[0].deploymentStatus.unavailableReplicas == 2
    assert workloads.data[0].containers[0].image == "registry:2.6"
    client.delete(app)
    wait_for_app_to_be_deleted(client, app)


def wait_for_workload(client, ns, timeout=60, count=0):
    start = time.time()
    interval = 0.5
    workloads = client.list_workload(namespaceId=ns)
    while len(workloads.data) != count:
        if time.time() - start > timeout:
            print(workloads)
            raise Exception('Timeout waiting for workload service')
        time.sleep(interval)
        interval *= 2
        workloads = client.list_workload(namespaceId=ns)
    return workloads


def wait_for_replicas(client, ns, timeout=60, count=0):
    start = time.time()
    interval = 0.5
    workloads = client.list_workload(namespaceId=ns)
    while workloads.data[0].deploymentStatus.replicas != count:
        if time.time() - start > timeout:
            print(workloads)
            raise Exception('Timeout waiting for workload replicas')
        time.sleep(interval)
        interval *= 2
        workloads = client.list_workload(namespaceId=ns)
    return workloads


def wait_for_app_to_be_deleted(client, app, timeout=120):
    start = time.time()
    interval = 0.5
    while True:
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for apps to be deleted")
        apps = client.list_app()
        found = False
        for a in apps:
            if a.id == app.id:
                found = True
                break
        if not found:
            break
        time.sleep(interval)
        interval *= 2


def wait_for_monitor_metric(admin_cc, admin_mc, timeout=60):
    client = admin_mc.client
    start = time.time()
    interval = 0.5
    monitorMetrics = client.list_monitor_metric(namespaceId=admin_cc.
                                                cluster.id)
    while len(monitorMetrics.data) == 0:
        if time.time() - start > timeout:
            print(monitorMetrics)
            raise Exception('Timeout waiting for monitorMetrics service')
        time.sleep(interval)
        interval *= 2
        monitorMetrics = client.list_monitor_metric(namespaceId=admin_cc.
                                                    cluster.id)
    found = False
    for m in monitorMetrics:
        if m.labels.component == "istio":
            found = True
            break
    if not found:
        raise AssertionError(
            "not found istio expression")
