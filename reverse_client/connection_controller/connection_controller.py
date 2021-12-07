from abc import abstractmethod


class ConnectionController():

	def __init__(self, interactive):
		self._interactive = interactive

	@property
	def interactive(self):
		return self._interactive

	@abstractmethod
	def request(self, *args, **kwargs):
		pass

	@abstractmethod
	def close(self):
		pass