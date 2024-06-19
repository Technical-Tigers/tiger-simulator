from asyncio import sleep
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uuid
from redis import Redis
from src.common import ObjectMeta, ListMeta, K8S_POD_STATUS
from src.utils.redis import RedisConnection
from src.utils.json import json_default, attribute_exists
from src.utils.utils import datetime_to_str
import json
from string import Template

API_VERSION: str = 'v1'
RESOURCE_VERSION: str = 'v1'

BATCH_NAME = Template('pod_${id}_batch')
STATS_NAME = Template('pod_${id}_stats')

class PodTemplateSpec:

    def __init__(self, json: Optional[dict[str, any]] = None):
        if (json is None):
            raise NotImplementedError
        # Additional fields for the simulator
        self.token_GPU: int = json['token_GPU']
        self.token_IO: int = json['token_IO']
        self.deployment_id: int = json['deployment_id']
        self.models: list[str] = json.get('models', [])

        self.metadata: ObjectMeta = ObjectMeta(
            json_default(json, 'metadata', {}))
        self.spec: V1PodSpec = V1PodSpec(json_default(json, 'spec', {}))


class V1Pod:

    def __init__(self, id: int, pod_template: Optional[PodTemplateSpec]):
        self.id: int = id
        self.token_GPU: int = pod_template.token_GPU
        self.token_IO: int = pod_template.token_IO
        self.deployment_id: int = pod_template.deployment_id
        self.models: list[str] = pod_template.models

        self.apiVersion: str = API_VERSION
        self.kind: str = "Pod"
        self.metadata: ObjectMeta = pod_template.metadata
        self.spec: V1PodSpec = pod_template.spec
        self.status: V1PodStatus = V1PodStatus({}, self.id)

    @staticmethod
    async def init_from_redis(id: int):
        async with RedisConnection() as r:
            pod_json: dict[str, any] = json.loads(
                (await r.get(f'pod_{id}')).decode('utf-8'))

            pod = V1Pod(id, PodTemplateSpec(pod_json))

            return pod

    async def save(self):
        async with RedisConnection() as r:
            await r.set(f'pod_{self.id}', self.toJson())

            # Check if pod id is saved in pod_ids
            await r.sadd("pod_ids", self.id)

    # async def delete(self):
    #     async with RedisConnection() as r:
    #         await r.delete(f'pod_{self.id}')

    #         # BUG: There is a possible race condition here
    #         pod_ids: List[int] = json.loads((await r.get("pod_ids")).decode('utf-8'))
    #         pod_ids.remove(self.id)
    #         await r.set("pod_ids", json.dumps(pod_ids))

    async def add_stats(self, new_stats: list[tuple[str, str]]):
        for i in range(len(new_stats)):
            new_stats[i] = json.dumps(new_stats[i])
        async with RedisConnection() as r:
            await r.rpush(STATS_NAME.substitute(id=self.id), *new_stats) 

    async def loadModel(self, model: str, load_time: float,
                        replace: List[str]):
        new_stats = []
        if replace is not None:
            for model_to_replace in replace:
                model_to_replace = model_to_replace.split('+')[-1]
                if model_to_replace in self.models:
                    self.models.remove(model_to_replace)
                    new_stats.append((f'{model_to_replace}#unload',
                                       datetime_to_str(datetime.now())))

        new_stats.append(
            (f'{model}#load_start', datetime_to_str(datetime.now())))
        await sleep(load_time)
        new_stats.append(
            (f'{model}#load_end', datetime_to_str(datetime.now())))

        self.models.append(model)
        await self.save()
        await self.add_stats(new_stats)

    async def inference(self, model: str, inference_time: float):
        print(f"Starting inference for {model} on pod {self.id} at {datetime.now()}", flush=True)
        new_stats = []
        new_stats.append(
            (f'{model}#inference_start', datetime_to_str(datetime.now())))

        await sleep(inference_time) 

        print(f"Finishing inference for {model} on pod {self.id} at {datetime.now()}", flush=True)
        new_stats.append(
            (f'{model}#inference_end', datetime_to_str(datetime.now())))

        await self.add_stats(new_stats)

    def start(self):
        pass

    def halt(self):
        pass

    def toJson(self):
        return json.dumps(self, default=vars)

    def recalculate_function(self, batch: dict[str, str], inference_id: uuid,
                             inference_time: float):
        # TODO: add actual function for 
        batch[str(inference_id)] = str(datetime.now() +
                                       timedelta(seconds=inference_time))
        return batch

    async def _recalculate_batch(self, inference_id: uuid,
                                 infernece_time: float):
        batch_name = BATCH_NAME.substitute(id=self.id)
        lock_name = f"lock:{batch_name}"
        async with RedisConnection() as r:
            # Try to acquire the lock
            async with r.lock(lock_name):

                # Once the lock is acquired, perform the operations
                batch = await r.hgetall(batch_name)
                recalculated_batch = self.recalculate_function(batch, inference_id, infernece_time)
                await r.hset(batch_name, mapping=recalculated_batch)

    async def _check_inference(self, inference_id: uuid) -> float:
        batch_name = BATCH_NAME.substitute(id=self.id)
        lock_name = f"lock:{batch_name}"
        redis_id = str(inference_id).encode('utf-8')
        
        async with RedisConnection() as r:
            async with r.lock(lock_name):
                batch = await r.hgetall(batch_name)
                if redis_id not in batch:
                    return 0
                time_left = (datetime.fromisoformat(
                    batch[redis_id].decode('utf-8')) -
                                datetime.now()).total_seconds()
                if time_left <= 0:
                    await r.hdel(batch_name, str(inference_id))
                    return 0.0
                return time_left


class V1PodSpec:

    def __init__(self, json):
        self.activeDeadlineSeconds: Optional[int] = json_default(
            json, 'active_deadline_seconds', None)
        self.affinity: Optional[V1Affinity] = V1Affinity(
            json['affinity']) if attribute_exists(json, 'affinity') else None
        self.automountServiceAccountToken: Optional[bool] = json_default(
            json, 'automount_service_account_token', None)
        self.containers: list[V1Container] = [
            V1Container(container)
            for container in json_default(json, 'containers', {})
        ]
        self.dnsConfig: Optional[V1PodDNSConfig] = V1PodDNSConfig(
            json['dns_config']) if attribute_exists(json,
                                                    'dns_config') else None
        self.dnsPolicy: Optional[str] = json_default(json, 'dns_policy', None)
        self.enableServiceLinks: Optional[bool] = json_default(
            json, 'enable_service_links', None)
        self.ephemeralContainers: Optional[list[V1EphemeralContainer]] = ([
            V1EphemeralContainer(container)
            for container in json['ephemeral_containers']
        ] if attribute_exists(json, 'ephemeral_containers') else None)
        self.hostAliases: Optional[list[V1HostAlias]] = ([
            V1HostAlias(alias) for alias in json['host_aliases']
        ] if attribute_exists(json, 'host_aliases') else None)
        self.hostIpc: Optional[bool] = json_default(json, 'host_ipc', None)
        self.hostNetwork: Optional[bool] = json_default(json, 'host_network',
                                                        None)
        self.hostPid: Optional[bool] = json_default(json, 'host_pid', None)
        self.hostUsers: Optional[bool] = json_default(json, 'host_users', None)
        self.hostname: Optional[str] = json_default(json, 'hostname', None)
        self.imagePullSecrets: Optional[list[V1LocalObjectReference]] = ([
            V1LocalObjectReference(secret)
            for secret in json['image_pull_secrets']
        ] if attribute_exists(json, 'image_pull_secrets') else None)
        self.initContainers: Optional[list[V1Container]] = ([
            V1Container(container) for container in json['init_containers']
        ] if attribute_exists(json, 'init_containers') else None)
        self.nodeName: Optional[str] = json_default(json, 'node_name', None)
        self.nodeSelector: Optional[dict[str, str]] = json_default(
            json, 'node_selector', None)
        self.os: Optional[str] = json_default(json, 'os', None)
        self.overhead: Optional[dict[str, str]] = json_default(
            json, 'overhead', None)
        self.preemptionPolicy: Optional[str] = json_default(
            json, 'preemption_policy', None)
        self.priority: Optional[int] = json_default(json, 'priority', None)
        self.priorityClassName: Optional[str] = json_default(
            json, 'priority_class_name', None)
        self.readinessGates: Optional[list[V1PodReadinessGate]] = ([
            V1PodReadinessGate(gate) for gate in json['readiness_gates']
        ] if attribute_exists(json, 'readiness_gates') else None)
        self.resourceClaims: Optional[list[V1PodResourceClaim]] = ([
            V1PodResourceClaim(claim) for claim in json['resource_claims']
        ] if attribute_exists(json, 'resource_claims') else None)
        self.restartPolicy: Optional[str] = json_default(
            json, 'restart_policy', None)
        self.runtimeClassName: Optional[str] = json_default(
            json, 'runtime_class_name', None)
        self.schedulerName: Optional[str] = json_default(
            json, 'scheduler_name', None)
        self.schedulingGates: Optional[list[V1SchedulingGate]] = ([
            V1SchedulingGate(gate) for gate in json['scheduling_gates']
        ] if attribute_exists(json, 'scheduling_gates') else None)
        self.securityContext: Optional[V1PodSecurityContext] = (
            V1PodSecurityContext(json['security_context']) if attribute_exists(
                json, 'security_context') else None)
        self.serviceAccount: Optional[str] = json_default(
            json, 'service_account', None)
        self.serviceAccountName: Optional[str] = json_default(
            json, 'service_account_name', None)
        self.setHostnameAsFqdn: Optional[bool] = json_default(
            json, 'set_hostname_as_fqdn', None)
        self.shareProcessNamespace: Optional[bool] = json_default(
            json, 'share_process_namespace', None)
        self.subdomain: Optional[str] = json_default(json, 'subdomain', None)
        self.terminationGracePeriodSeconds: Optional[int] = json_default(
            json, 'termination_grace_period_seconds', None)
        self.tolerations: Optional[list[V1Toleration]] = ([
            V1Toleration(toleration) for toleration in json['tolerations']
        ] if attribute_exists(json, 'tolerations') else None)
        self.topologySpreadConstraints: Optional[
            list[V1TopologySpreadConstraint]] = ([
                V1TopologySpreadConstraint(constraint)
                for constraint in json['topology_spread_constraints']
            ] if attribute_exists(json, 'topology_spread_constraints') else
                                                 None)
        self.volumes: Optional[list[V1Volume]] = ([
            V1Volume(volume) for volume in json['volumes']
        ] if attribute_exists(json, 'volumes') else None)


class V1Affinity:

    def __init__(self, json):
        pass


class V1Container:

    def __init__(self, json):
        self.name: str = json_default(json, 'name', 'unknown-container')
        self.resources = json_default(json, 'resources', {})
        pass


class V1PodDNSConfig:

    def __init__(self, json):
        self.nameservers: list[str] = json['nameservers']
        self.options: list[V1PodDNSConfigOption] = []
        self.searches: list[str] = json['searches']


class V1PodDNSConfigOption:

    def __init__(self, json):
        self.name: str = json['name']
        self.value: str = json['value']


class V1EphemeralContainer:

    def __init__(self, json):
        pass


class V1HostAlias:

    def __init__(self, json):
        pass


class V1LocalObjectReference:

    def __init__(self, json):
        pass


class V1PodResourceClaim:

    def __init__(self, json):
        pass


class V1SchedulingGate:

    def __init__(self, json):
        pass


class V1PodReadinessGate:

    def __init__(self, json):
        pass


class V1PodSecurityContext:

    def __init__(self, json):
        self.fs_group: int = json['fsGroup']
        self.fs_group_change_policy: str = json['fsGroupChangePolicy']
        self.run_as_group: int = json['runAsGroup']
        self.run_as_non_root: bool = json['runAsNonRoot']
        self.run_as_user: int = json['runAsUser']
        self.se_linux_options: V1SELinuxOptions = V1SELinuxOptions(
            json['seLinuxOptions'])
        self.seccomp_profile: V1SeccompProfile = V1SeccompProfile(
            json['seccompProfile'])
        self.supplemental_groups: list[int] = json['supplementalGroups']
        self.sysctls: list[V1Sysctl] = []
        self.windows_options: V1WindowsSecurityContextOptions = V1WindowsSecurityContextOptions(
            json['windowsOptions'])


class V1SELinuxOptions:

    def __init__(self, json):
        self.level: str = json['level']
        self.role: str = json['role']
        self.type: str = json['type']
        self.user: str = json['user']


class V1SeccompProfile:

    def __init__(self, json):
        self.localhost_profile: str = json['localhostProfile']
        self.type: str = json['type']


class V1Sysctl:

    def __init__(self, json):
        self.name: str = json['name']
        self.value: str = json['value']


class V1WindowsSecurityContextOptions:

    def __init__(self, json):
        self.gmsa_credential_spec: str = json['gmsaCredentialSpec']
        self.gmsa_credential_spec_name: str = json['gmsaCredentialSpecName']
        self.host_process: bool = json['hostProcess']
        self.run_as_user_name: str = json['runAsUserName']


class V1Toleration:

    def __init__(self, json):
        pass


class V1TopologySpreadConstraint:

    def __init__(self, json):
        pass


class V1Volume:

    def __init__(self, json):
        pass


class V1PodStatus:

    def __init__(self, json, id):
        self.phase: str = json_default(json, 'phase',
                                       K8S_POD_STATUS.RUNNING.value)
        self.conditions: list[V1PodCondition] = json_default(
            json, 'conditions', [V1PodCondition({})])
        # Set pod ip to current ip
        self.podIP: str = id


class V1PodCondition:

    def __init__(self, json):
        self.status: str = json_default(json, 'status', 'True')
        self.type: str = json_default(json, 'type', 'Ready')


class PodList:

    def __init__(self, pods: list[V1Pod]):
        self.apiVersion: str = API_VERSION
        self.items: list[V1Pod] = pods
        self.kind: str = 'PodList'
        self.metadata: ListMeta = ListMeta()
        # doesn't seem to be used now, but we might need it in the future
