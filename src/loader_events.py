import typing as t
from enum import Enum


class LoaderStatusEnum(Enum):
	BOOT_FAILED = -3
	UPLOAD_FAILED = -2
	CONNECTION_FAILED = -1
	EXITED = 0
	CONNECTING = 1
	UPLOADING = 2
	BOOTING = 3
	KEEP_ALIVE = 4

class LoaderStatus():
	node_id = ""
	status = None

	def __init__(self, node_id, status):
		self.node_id=node_id
		self.status=LoaderStatusEnum(status)

# Handled exclusively by NodeDescriptor, then passed on as a Node_LoaderStatusMessage
# This is because the LoadWorker class doesn't know anything about the NodeDescriptor that is managing it.
class Node_LoaderStatusCodeMessage(t.NamedTuple):
	payload: LoaderStatusEnum

class Node_LoaderStatusMessage(t.NamedTuple):
	payload: LoaderStatus

class Node_LoaderUploadPctMessage(t.NamedTuple):
	#[node_id, % complete]
	payload: t.List[str]

class Node_LoaderExceptionMessage(t.NamedTuple):
	# [node_id, message]
	payload: t.List[str]

class Node_UploadCommandMessage(t.NamedTuple):
    payload: t.List[str]

