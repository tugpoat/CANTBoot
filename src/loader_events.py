import typing as t
from enum import Enum

# Handled exclusively by NodeDescriptor, then passed on as a Node_LoaderStatusMessage
# This is because the LoadWorker class doesn't know anything about the NodeDescriptor that is managing it.
class Node_LoaderStatusCodeMessage(t.NamedTuple):
	payload: int

class Node_LoaderStatusMessage(t.NamedTuple):
	payload: t.List[str]

class Node_LoaderUploadPctMessage(t.NamedTuple):
	#[node_id, % complete]
	payload: t.List[str]

class Node_LoaderExceptionMessage(t.NamedTuple):
	# [node_id, message]
	payload: t.List[str]

class Node_UploadCommandMessage(t.NamedTuple):
    payload: t.List[str]

