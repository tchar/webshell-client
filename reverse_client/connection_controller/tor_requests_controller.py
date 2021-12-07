import requests
from stem import Signal, SocketError
from stem.control import Controller
import logging
from threading import Timer, Lock
from .exceptions import TorConnectionError, TorRenewConnectionError
from .requests_controller import RequestsController
from requests.exceptions import ConnectionError


class TorRequestsController(RequestsController):

	def __init__(self, uri, shell_io, method, 
				post_body_format, command_key, token_key, token,
				tor_ip, tor_port, tor_control_port,
				tor_control_password, tor_refresh_ip_every):
		
		super(TorRequestsController, self).__init__(
			uri, shell_io, method, 
			post_body_format, command_key, token_key, token
		)
		shell_io.info("TorRequests: Initiating")
		shell_io.debug(f"TorRequests: socks5://{tor_ip}:{tor_port}")
		self._shell_io = shell_io
		self._tor_ip = tor_ip
		self._tor_port = tor_port
		self._tor_control_port = tor_control_port
		self._tor_control_password = tor_control_password
		self._tor_refresh_ip_every = tor_refresh_ip_every

		self._lock = Lock()
		self._conn_error = None

		
		timer = Timer(1, self._callback)
		timer.daemon = True
		timer.start()

	def _callback(self):
		with self._lock:
			try:
				succeed = self._renew_connection()
			except SocketError as e:
				succeed = False

		if not succeed:
			msg = "Could not connect to tor, is your tor service running?"
			self._shell_io.warning(msg)			

		timer = Timer(self._tor_refresh_ip_every, self._callback)
		timer.daemon = True
		timer.start()

	def request(self, cmd):
		with self._lock:
			session = requests.session()


		session.proxies = {
			"http":  f"socks5://{self._tor_ip}:{self._tor_port}",
			"https": f"socks5://{self._tor_ip}:{self._tor_port}"
		}
		try:
			response = super(TorRequestsController, self).request(session, cmd)

			return RequestsController._process_response(response)
		except ConnectionError as e:
			raise TorConnectionError(e)
		except Exception as e:
			print(type(e))
			exit(0)

	# signal TOR for a new connection 
	def _renew_connection(self, run_dry=False):
		self._shell_io.info("Renewing tor connection")
		with Controller.from_port(port=self._tor_control_port) as controller:
			controller.authenticate(password=self._tor_control_password)

			if run_dry:
				return True

			# controller.signal(Signal.NEWNYM)
		return True

	def _test_ip(self):
		session = requests.session()
                # http://icanhazip.com/
		session.proxies = {
			"http":  f"socks5://{self._tor_ip}:{self._tor_port}",
			"https": f"socks5://{self._tor_ip}:{self._tor_port}"
		}
		print(session.get("http://httpbin.org/ip"))


# https://stackoverflow.com/questions/30286293/make-requests-using-python-over-tor
# # Make a request through the Tor connection
# # IP visible through Tor
# import time
# t = TorRequests()
# session = t.get_session()
# print(session.get("http://httpbin.org/ip").text)
# time.sleep(10)
# # Above should print an IP different than your public IP
# session = t.get_session()
# print(session.get("http://httpbin.org/ip").text)


# # Following prints your normal public IP
# print(requests.get("http://httpbin.org/ip").text)
# renew_connection()
# session = t.get_session()
# print(session.get("http://httpbin.org/ip").text)
