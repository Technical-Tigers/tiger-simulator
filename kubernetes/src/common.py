from src.utils.json import json_default
from enum import Enum


# enums from scheduler
class DeploymentStatus(str, Enum):
    STARTING = "STARTING"
    READY = "READY"
    INVALID = "INVALID"
    CRASHED = "CRASHED"
    SLEEPING = "SLEEPING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"


class K8S_POD_STATUS(str, Enum):
    RUNNING = "Running"
    PENDING = "Pending"
    TERMINATING = "Terminating"
    UNKNOWN = "Unknown"
    FAILED = "Failed"
    SUCCEDED = "Succeeded"


class ObjectMeta:

    def __init__(self, meta_json: dict[str, any]):
        self.annotations: dict[str, str] = json_default(meta_json,
                                                        'annotations', {})
        self.name: str = json_default(meta_json, 'name', 'no-name')
        self.namespace: str = 'schedulerSimulatorNamespace'
        self.labels: dict[str, str] = json_default(meta_json, 'labels', {})

        ### Unmocked fields (or not mocked properly)
        # self.creationTimestamp: datetime = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        # self.deletionGracePeriodSeconds: int = 30
        # self.deletionTimestamp: datetime = None
        # self.finalizers: list[str] = []
        # self.generateName: str = ''
        # self.generation: int = -1
        # self.managedFields: list = list()
        # self.ownerReferences: list = list()
        # self.resourceVersion: str = datetime.now()
        # self.selfLink: str = ''
        # self.uid: str = json_default(meta_json, 'uid', uuid.uuid4())


class ListMeta:

    def __init__(self,
                 contiune: str = '',
                 remainingItemCount: int = 0,
                 resourceVersion: str = '',
                 selfLink: str = ''):
        setattr(self, 'continue', contiune)
        self.remainingItemCount: int = remainingItemCount
        self.resourceVersion: str = resourceVersion
        self.selfLink: str = selfLink
