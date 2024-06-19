from redis import Redis
from src.pod import PodTemplateSpec, V1Pod
from src.common import ObjectMeta
from src.utils.redis import RedisConnection
from src.utils.json import json_default
import json
import random
import os

from src.utils.logger import Logger

DOCKER_TAG = os.environ.get("DOCKER_TAG", "")
DEPLOYMENT_RANDOM_ID = os.environ.get("DEPLOYMENT_RANDOM_ID", "2137")
API_VERSION: str = 'v1'
RESOURCE_VERSION: str = 'v1'


class Deployment:

    def __init__(self, id: int, dep_json: dict[str, any]):
        self.id: int = id

        # Additional fields for the simulator
        self.pod_ids: list[int] = dep_json.get('pod_ids', [])

        self.apiVersion: str = API_VERSION
        self.kind: str = dep_json['kind']
        self.metadata: ObjectMeta = ObjectMeta(dep_json['metadata'])
        self.spec: DeploymentSpec = DeploymentSpec(id, dep_json['spec'])
        self.status: DeploymentStatus = DeploymentStatus(dep_json['status'])

    @staticmethod
    async def init_from_redis(id: int):
        async with RedisConnection() as r:
            dep_json: dict[str, any] = json.loads(
                (await r.get(f'dep_{id}')).decode('utf-8'))
            return Deployment(id, dep_json)

    def start(self):
        pass

    def halt(self):
        pass

    async def patch(self, patch: dict[str, any]):
        starting = json.loads(self.toJson())

        self._update_only_needed(patch, starting)
        self.__init__(self.id, starting)
        await self.save()

    async def create_pod(self) -> V1Pod:
        id: int = random.randint(0, 1000000)
        pod: V1Pod = V1Pod(id, self.spec.template)
        await pod.save()
        self.pod_ids.append(id)
        await self.save()
        return pod

    async def balance_pods(self):
        target_pods = self.spec.replicas

        # Create pods if missing
        while (target_pods > len(self.pod_ids)):
            pod = await self.create_pod()
            Logger.info("Creating missing pods %s", pod.id)

        # Delete pods if too many
        # BUG: This will only delete a pod if there is an idle pod. Otherwise
        # it will only change the number of replicas but not delete any pods.
        # for pod_id in self.pod_ids:
        #     if (target_pods >= len(self.pod_ids)):
        #         break

        #     pod = await V1Pod.init_from_redis(pod_id)
        #     if pod.status.phase == "Idle":
        #         await pod.delete()
        #         self.pod_ids.remove(pod_id)
        #         print(f"Deleting idle pod {pod_id}", flush=True)

    def toJson(self):
        return json.dumps(self, default=vars)

    def _update_only_needed(self, patch: dict, starting: dict):
        for key, value in patch.items():
            try:
                if isinstance(value, dict):
                    if key not in starting:
                        starting[key] = value
                    else:
                        self._update_only_needed(value, starting[key])
                else:
                    starting[key] = value
            except Exception as e:
                Logger.warning(
                    "Error updating key: %s with value: %s in %s\nError: %s",
                    key, value, starting, e)
                continue

    async def save(self):
        await self.balance_pods()

        async with RedisConnection() as r:
            await r.set(f'dep_{self.id}', self.toJson())

            # Save deployment id to redis
            await r.sadd("dep_ids", self.id)


class DeploymentSpec:

    def __init__(self, deployment_id: int, spec_json: dict[str, any]):
        self.minReadySeconds: int = json_default(spec_json, 'minReadySeconds',
                                                 0)
        self.progressDeadlineSeconds: int = json_default(
            spec_json, 'progressDeadlineSeconds', 600)
        self.replicas: int = json_default(spec_json, 'replicas', 1)
        self.revisionHistoryLimit: int = json_default(spec_json,
                                                      'revisionHistoryLimit',
                                                      10)
        self.selector: LabelSelector = LabelSelector()
        spec_pod_template: dict[str,
                                any] = json_default(spec_json, 'template', {})
        spec_pod_template['deployment_id'] = deployment_id
        self.template: PodTemplateSpec = PodTemplateSpec(spec_pod_template)

        ### Unmocked fields (or not mocked properly)
        # self.paused: bool = False
        # self.strategy = None


class DeploymentStatus:

    def __init__(self, json: dict[str, any]):
        ### Unmocked fields (or not mocked properly)
        # self.available_replicas: int = json_default(json, 'available_replicas', 0)
        # self.collision_count: int = json_default(json, 'collision_count', 0)
        # self.conditions: list = []
        # self.observedGeneration: int = json_default(json, 'observedGeneration', 0)
        # self.readyReplicas: int = json_default(json, 'readyReplicas', 0)
        # self.replicas: int = json_default(json, 'replicas', 0)
        # self.unavailableReplicas: int = json_default(json, 'unavailableReplicas', 0)
        # self.updatedReplicas: int = json_default(json, 'updatedReplicas', 0)
        pass


class LabelSelector:

    def __init__(self, json: dict[str, any] = None):
        self.matchExpressions: list = []
        self.matchLabels: dict[str, str] = {}

        if json is not None:
            self.matchExpressions: list = json_default(json, 'matchExpressions',
                                                       [])
            self.matchLabels: dict[str,
                                   str] = json_default(json, 'matchLabels', {})
