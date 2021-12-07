import socket
from threading import Thread
from ..utils import get_ip_port
from .connection_controller import ConnectionController
from .exceptions import SocketConnectionError
import time


class SocketClientController(ConnectionController):

	def __init__(self, uri, shell_io, *args, **kwargs):

		super(SocketClientController, self).__init__(interactive=True)

		self._uri = uri
		self._ip, self._port =  get_ip_port(uri)
		self._shell_io = shell_io

		self._connected = False

		self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# self._socket.setblocking(False)
		# self._socket.settimeout(0.5)
		Thread(target=self._listener_thread).start()


	def _connect(self, silent=False):
		try:
			self._socket.connect((self._ip, self._port))
			self._connected = True
			self._shell_io.info(f"Connected to {self._uri}")
			return True
		except (ConnectionRefusedError, ConnectionAbortedError) as e:
			if not silent:
				self._shell_io.error(f"Could not connect to socket {self._uri}")
			self._connected = False
			return False

	def _listener_thread(self):
		while True:
			connected = self._connected
			if not connected:
				connected = self._connect(silent=True)
				
			if not connected:
				time.sleep(0.5)
				continue

			data = self._socket.recv(1024)
			data = data.decode("utf-8")
			data = data.split("\n");
			data = map(lambda x: x.strip(), data)
			data = filter(lambda x: x != "", data)
			data = list(data)
			try:
				data, prompt = data[:-1], data[-1]
			except IndexError:
				prompt = ""
			data = "\n".join(data)
			# data = data + "\n" + prompt
			# time.sleep(1)
			# ss = self._shell_io._shell_session
			# print('Before', ss.message)
			print([prompt])
			prompt = self._shell_io.text_with_ansi(prompt)
			self._shell_io._shell_session.message = prompt
			# setattr(self._shell_io._shell_session, 'message', prompt)
			# print('After', ss.message)

			# for item in dir(self._shell_io._shell_session):
				# attr = getattr(self._shell_io._shell_session, item)
				# print(item, attr)
			# continue

			# if data:
				# print(data, end='')


	def _request_thread(self, cmd):
		connected = self._connected
		
		if not self._connected:
			connected = self._connect(silent=True)

		if not connected:
			return self._shell_io.error(f"Could not connect to socket {self._uri}")

		if not cmd.endswith("\n"):
			cmd += "\n"
		cmd = cmd.encode("utf-8")

		try:
			sent = self._socket.send(cmd)
		except (OSError, BrokenPipeError) as e:
			self._connected = False
			self._shell_io.error(e)

	def request(self, cmd):
		Thread(target=self._request_thread, args=(cmd,)).start()


	def close(self):
		try:
			self._socket.shutdown(socket.SHUT_WR)
		except:
			pass
		self._socket.close()

# python -c 'import pty;pty.spawn("/bin/bash")'