import os
import sys
import traceback
from enum import Enum
from base64 import b64decode
from .exceptions import ShellException, ShellInternalInterrupt
from .connection_controller.exceptions import (
	RequestError, 
	TorConnectionError,
	TorRenewConnectionError,
	SocketConnectionError
)

class Shell():

	_default_aliases = {
		"ll": "ls -l",
		"la": "ls -a"
	}

	class Type(Enum):	
		INTERACTIVE = 1
		VIRTUAL_ON = 2
		VIRTUAL_OFF = 3
		VIRTUAL_FORCE = 4

		@classmethod
		def to_type(cls, s):
			if s == "interactive":
				return cls.INTERACTIVE
			elif s == "virtual-on":
				return cls.VIRTUAL_ON
			elif s == "virtual-off":
				return cls.VIRTUAL_OFF
			elif s == "virtual-force":
				return cls.VIRTUAL_FORCE
			else:
				raise NotImplementedError(f"{s} is not supported")


	def __init__(self, 
				uri,
				virtual,
				last_line,
				io,
				connection_controller,
				internal_commands):

		io.info("Shell: Initiating")		
		self._uri = uri
		self._last_line = last_line
		self._io = io
		self._connection_controller = connection_controller
		self._internal_commands = internal_commands

		self._user = None
		self._hostname = None
		self._cwd = None
		self._reset()

		if connection_controller.interactive:
			self._type = Shell.Type.to_type("interactive")
		else:
			self._type = Shell.Type.to_type(f"virtual-{virtual}")

		self._aliases = Shell._default_aliases

		if self._type == Shell.Type.VIRTUAL_FORCE:
			io.print(
				"Setting virtual to force may have unpredicted behaviour, " +
				"try setting it to on or off first"
			)


	@property
	def _input_txt(self):
		user = self._user or "shell"
		hostname = f"@{self._user}" if self._user else ""
		cwd = self._cwd or ""

		if self._user is not None and cwd.startswith(f"/home/{user}"):
			cwd = cwd.replace(f"/home/{user}", "~")
		
		io = self._io
		return (io.input_text_color(f"{user}{hostname}", "blue") +
			io.input_text_color(":") + 
			io.input_text_color(f"{cwd}", "green") + 
			io.input_text_color("$ ")
		)

	def _set_user(self, user):
		self._user = user
		return self

	def _set_cwd(self, new_cwd):
		if os.path.isabs(new_cwd):
			self._cwd = new_cwd
		elif self._cwd is not None:
			new_cwd = os.path.join(self._cwd, new_cwd)
			new_cwd = os.path.normpath(new_cwd)
			self._cwd = str(new_cwd)
		else:
			pass
		return self

	def _set_command(self, cmd):
		self._command = {
			"real": cmd,
			"exec": cmd,
			"exec_no_pipe": cmd
		}
		return self

	def _make_aliases(self):
		cmd = self._command["exec_no_pipe"]
		for key, val in self._aliases.items():
			if cmd.startswith(key):
				cmd = cmd.replace(key, val, 1)
		self._command["exec_no_pipe"] = cmd
		return self
	
	def _change_directory(self):
		if self._type not in [Shell.Type.VIRTUAL_ON, Shell.Type.VIRTUAL_FORCE]:
			return self
		cmd = self._command["exec_no_pipe"]
		if self._cwd is not None:
			cmd = f"cd {self._cwd} && {cmd}"
		self._command["exec_no_pipe"] = cmd
		return self

	def _redirect_stderr_to_stdout(self):
		cmd = self._command["exec_no_pipe"]
		# if self._type in [Shell.Type.VIRTUAL_ON, Shell.Type.VIRTUAL_FORCE]:
			# cmd = f"{cmd} 2>&1"
		self._command["exec"] = cmd
		return self


	def _get_user_input(self, custom_input=None):
		if custom_input is None:
			user_input = self._io.shell_input(self._input_txt, save_history=True)
		else:
			user_input = custom_input

		if user_input is None or user_input.strip() == "":
			raise ShellInternalInterrupt()

		user_input = user_input.strip()

		if user_input.startswith(":"):
			if self._type == Shell.Type.VIRTUAL_OFF:
				raise ShellException("Inernal commands are not enabled when virtual is set to off")
			cmd, cmd_name = self._internal_commands.execute(user_input)
			self._request["internal_command"] = cmd_name
			return self._set_command(cmd)._change_directory()._redirect_stderr_to_stdout()

		if self._type in [Shell.Type.VIRTUAL_ON, Shell.Type.VIRTUAL_FORCE]:
			user_input_list = user_input.split("&&")
			user_input = user_input_list[0].strip()
			if len(user_input_list) != 1:
				self._io.warning(f"Enabling features runs only one command command will be {user_input}")

		self._io.add_to_shell_history(user_input)

		return (self._set_command(user_input)
			._make_aliases()
			._change_directory()
			._redirect_stderr_to_stdout())

	def _should_make_request(self):
		real_cmd = self._command["real"]
		make_request = True
		if real_cmd == "clear":
			self._io.clear()
			make_request = False

		self._request["skipped"] = not make_request
		return make_request

	def _make_request(self):
		cmd = self._command["exec"]
		real_cmd = self._command["real"]

		if cmd is None:
			raise ShellException("Command is None")

		if cmd.strip() == "":
			raise ShellException("Command is empty")

		if not self._should_make_request():
			self._io.debug(f"Not making request with cmd: {real_cmd}")
			return self

		self._io.info(f"Exec Command -> {cmd}")

		if self._type == Shell.Type.INTERACTIVE:
			self._connection_controller.request(cmd)
			raise ShellInternalInterrupt()
		else:
			data, status = self._connection_controller.request(cmd)

		if status != 200:
			self._io.print(f"Data: {data}")
			self._io.error(f"Status_code: {status}")

		self._request["response"] = {
			"data": data,
			"status": status
		}

		return self

	def _process_internal_command_response(self):
		cmd_name = self._request["internal_command"] 
		if cmd_name.startswith("sendfile"):
			self._request["internal_command"] = None
			return self._process_response()
		
		if self._last_line == "command-result" and self._request["command_result"] != "0":
			raise ShellException(f"Command returned with an exit code {command_result}")

		if cmd_name.startswith("getfile"):
			targetpath = cmd_name.split(":")[-1]
			if cmd_name.startswith("getfileraw"):
				mode, b64 = "w", False
			else:
				mode, b64 = "wb", True
			try:
				data = b64decode(self._request["command_output"]) if b64 else self._request["command_output"]
				with open(targetpath, mode) as f:
					f.write(data)

				io = self._io
				io.print_with_color(
					f"Downloaded file to {targetpath}", "yellow"
				)
			except Exception as e:
				raise ShellException(e)
			return self

		else:
			raise NotImplementedError(f"{cmd_name} is not an internal command")


	def _process_response(self, force=False):
		if self._request["response"] is None:
			if not self._request["skipped"]:
				raise ShellException("Response is None")
			return self

		response_content = self._request["response"]["data"]
		response_content = response_content.split("\n")
		response_content = list(response_content)		

		if self._type not in [Shell.Type.INTERACTIVE, Shell.Type.VIRTUAL_ON, Shell.Type.VIRTUAL_FORCE]:
			command_output = "\n".join(response_content)
			self._request["command_output"] = command_output
			return self

		if self._last_line == "command":
			command_output = "\n".join(response_content)
			command_result = None
		elif self._last_line == "command-result":
			command_output = response_content[:-1]
			command_output = "\n".join(command_output)
			try:
				command_result = response_content[-1]
			except IndexError:
				command_result = None
		else:
			raise NotImplementedError(f"{self._last_line} parsing is not implemented")

		self._request["command_output"] = command_output
		self._request["command_result"] = command_result

		if self._request["internal_command"] is not None:
			self._process_internal_command_response()
			return self

		if self._last_line == "command" and self._type == Shell.Type.VIRTUAL_ON:
			return self

		if self._type != Shell.Type.INTERACTIVE and command_result != "0" and not force:
			self._io.error(f"Command returned a non zero exit code {command_result}")
			return self
		if not force and command_result != None:
			self._io.warning(f"Command returned an exit code {command_result}")	

		cmd = self._command["real"]
		
		if cmd.startswith("su "):
			self._set_user(None)
		elif cmd == "whoami":
			self._set_user(command_output)
		elif cmd.startswith("cd "):
			directory = cmd.replace("cd ", "", 1)
			directory = directory.strip()
			self._set_cwd(directory)
		elif cmd == "pwd":
			self._set_cwd(command_output)
		

		return self

	def _print_response(self):

		if self._request["internal_command"] is not None:
			return self

		if self._request["command_output"] is not None:
			command_output = self._request["command_output"]
		elif self._request["response"] is not None:
			command_output = self._request["response"]["data"]
		else:
			command_output = None

		if command_output is None:
			if not self._request["skipped"]:
				raise ShellException("Response is None")
			return self

		command_result = self._request["command_result"]
		
		if command_output:
			print(command_output)
		elif command_result != "0":
			self._io.error("Response content is empty")
		return self

	def _reset(self):
		self._command = {
			"real": None,
			"exec": None,
			"exec_no_pipe": None
		}
		self._request = {
			"command_output": None,
			"command_result": None,
			"response": None,
			"skipped": None,
			"internal_command": None
		}
		return self

	def _prompt_exit(self, msg, color):
		io = self._io
		io.print("\n")
		try:
			answer = self._io.shell_input(
				io.input_text_color(msg, color),
				save_history=False,
				valid_input=["yes", "y", "n", "no"]
			)
		except KeyboardInterrupt:
			self._exit()
		
		return answer.lower() in ["y", "yes"]
		

	def _exit(self):
		self._connection_controller.close()	
		sys.exit()


	def _pre_start(self):

		if (self._type in [Shell.Type.INTERACTIVE, Shell.Type.VIRTUAL_FORCE] 
			or (self._type == Shell.Type.VIRTUAL_ON and
				self._last_line == "command-result")):
			pre_commands = ["whoami", "pwd"]
		else:
			pre_commands = []

		for pre_command in pre_commands:
			try:
				(self._get_user_input(pre_command)
				._make_request()
				._process_response(force=True)
				._reset())
			except ShellInternalInterrupt:
				pass
			except (ShellException, NotImplementedError) as e:
				self._io.error(e)
			except TorConnectionError as e:
				self._io.error(e)
			except RequestError as e:
				self._io.error(e)
			except SocketConnectionError as e:
				self._io.error(e)
			except Exception as e:
				traceback.print_exc()
				should_exit = self._prompt_exit(
					f"Got an exception do you want to quit? (Y/n)> ",
					"error"
				)
				if should_exit:
					return False
			finally:
				self._reset()
		return True

	def start(self):

		if self._type == Shell.Type.INTERACTIVE:
			pass
		elif not self._pre_start():
			return self._exit()

		while True:
			try:
				(self._get_user_input()
					._make_request()
					._process_response()
					._print_response()
					._reset())

			except ShellInternalInterrupt:
				pass
			except (ShellException, NotImplementedError) as e:
				self._io.error(e)
			except RequestError as e:
				self._io.error(e)
			except TorConnectionError as e:
				self._io.error(e)
			except SocketConnectionError as e:
				self._io.error(e)
			except KeyboardInterrupt:
				return self._exit()
				yes = self._prompt_exit(
					"Are you sure you want to quit? (Y/n)> ",
					"green"
				)
				if yes:
					return self._exit()
				
			except Exception as e:
				traceback.print_exc()
				yes = self._prompt_exit(
					f"Got an exception do you want to quit? (Y/n)> ",
					"error"
				)
				if yes:
					self._connection_controller.close()
					return self._exit()
			finally:
				self._reset()