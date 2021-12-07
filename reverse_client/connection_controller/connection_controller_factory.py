from ..utils import url_regex, socket_regex
from .requests_controller import DefaultRequestsController
from .tor_requests_controller import TorRequestsController
from .socket_client_controller import SocketClientController


class ConnectionControllerFactory():

	@classmethod
	def get_connection_controller(cls, controller_str, *args, **kwargs):
		
		if controller_str == "default-requests":
			return DefaultRequestsController(*args, **kwargs)
		elif controller_str == "tor-requests":
			return TorRequestsController(*args, **kwargs)
		elif controller_str == "socket-client":
			return SocketClientController(*args, **kwargs)
		else:
			raise NotImplementedError("Not implemented")

	