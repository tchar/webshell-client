import traceback
from .connection_controller import ConnectionController
import requests
import json
from .exceptions import RequestError

class RequestsController(ConnectionController):

	_headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0",
		"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
		"Accept-Language":"en-US,en;q=0.5",
		"Accept-Encoding":"gzip, deflate",
		"Connection":"close",
		"Upgrade-Insecure-Requests":"1"
	}

	def __init__(self, uri, shell_io, method, post_body_format,
		command_key, token_key, token):

		super(RequestsController, self).__init__(interactive=False)

		self._uri = uri
		self._shell_io = shell_io
		self._method = method
		self._post_body_format = post_body_format
		self._command_key = command_key
		self._token_key = token_key
		self._token = token

	def request(self, session, cmd):
		return self._make_request(session, cmd)

	def _make_request(self, session, cmd):
		body = {
			self._command_key: cmd
		}

		headers = RequestsController._headers

		if self._token is not None:
			body[self._token_key] = self._token

		if self._method.upper() == "GET":
			self._shell_io.debug(f"Doing GET at {self._uri} and parameters: {json.dumps(body)}")
			return session.request("GET", self._uri, headers=headers, params=body)
		if self._method.upper() == "POST":
			if self._post_body_format == "x-www-urlencoded":
				self._shell_io.debug(f"Doing POST at {self._uri} and body: {json.dumps(body)}")
				return session.request("POST", self._uri, headers=headers, data=body)
			elif self._post_body_format == "json":
				self._shell_io.debug(f"Doing POST at {self._uri} and json: {json.dumps(body)}")
				return session.request("POST", self._uri, headers=headers, json=body)
			else:
				raise NotImplementedError(f"{self._post_body_format} not implemented for method POST")
		else:
			raise NotImplementedError(f"{self._method} not implemented")
	
	@classmethod	
	def _process_response(cls, response):
		response_content = response.content.decode("utf-8")
		status_code = response.status_code

		response_content = response_content.split("\\n");
		response_content = map(lambda x: x.strip(), response_content)
		response_content = filter(lambda x: x != "", response_content)
		response_content = "\n".join(response_content)

		return response_content, status_code

class DefaultRequestsController(RequestsController):

	def __init__(self, uri, shell_io, method, post_body_format,
		command_key, token_key, token, *args, **kwargs):
		
		super(DefaultRequestsController, self).__init__(
			uri, shell_io, method, post_body_format,
			command_key, token_key, token
		)

	def request(self, cmd):
		try:
			response = super(DefaultRequestsController, self).request(requests, cmd)
			
			return RequestsController._process_response(response)

		except Exception as e:
			raise RequestError(e)