import typing as t
from enum import Enum

class LoaderStatus(Enum):
	BOOT_FAILED = -3
	UPLOAD_FAILED = -2
	CONNECTION_FAILED = -1
	EXITED = 0
	CONNECTING = 1
	UPLOADING = 2
	BOOTING = 3
	KEEP_ALIVE = 4


class Node_LoaderStatusCodeMessage(t.NamedTuple):
	payload: LoaderStatus

class Node_LoaderUploadPctMessage(t.NamedTuple):
	payload: int

class Node_LoaderExceptionMessage(t.NamedTuple):
	payload: str

class Node_UploadCommandMessage(t.NamedTuple):
	payload: t.List[str]
