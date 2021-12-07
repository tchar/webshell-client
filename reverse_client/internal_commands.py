import logging
import os
import subprocess
import platform
import getpass
from .utils import tokenize
from base64 import b64encode
from .exceptions import ShellException, ShellInternalInterrupt

available_commands = ["sendfile", "getfile", "getfileraw"]

class InternalCommands():

	def __init__(self, shell_io):
		self._io = shell_io

	def _parse_command(self, command):
		return tokenize(" ")("\\")(command)


	def _sendfile(self, command):
		if len(command) != 3:
			raise ShellException(f"Expected 2 arguments, got {len(command) - 1}")

		filepath = command[1]
		targetpath = command[2]
		try:
			with open(filepath, "rb") as f:
				data = f.read()
		except Exception as e:
			raise ShellException(e)
		
		data = b64encode(data)
		data = data.decode("utf-8")
		return f"echo {data} | base64 -d > {targetpath}", command[0]

	def _getfile_raw(self, command):
		if len(command) != 3:
			raise ShellException(f"Expected 2 arguments, got {len(command) - 1}")

		filepath = command[1]
		targetpath = command[2]
		targetpath = os.path.abspath(targetpath)
		try:
			with open(targetpath, "w"):
				pass
		except Exception as e:
			raise ShellException(e)
		return f"cat {filepath}", f"{command[0]}:{targetpath}"


	def _getfile(self, command):
		if len(command) != 3:
			raise ShellException(f"Expected 2 arguments, got {len(command) - 1}")

		filepath = command[1]
		targetpath = command[2]
		targetpath = os.path.abspath(targetpath)
		try:
			with open(targetpath, "w"):
				pass
		except Exception as e:
			raise ShellException(e)
		return f"cat {filepath} | base64", f"{command[0]}:{targetpath}"

	def _run_command(self):
			user = getpass.getuser()
			hostname = platform.node()
			cwd = os.getcwd()

			command = self._io.external_shell_input("> ")
			command = command.strip()
			if command.strip() in ["exit", ""]:
				raise ShellInternalInterrupt()
			if command.strip() == "clear":
				return "clear", None

			proc = subprocess.Popen(
				command,
			    stdout = subprocess.PIPE,
			    stderr = subprocess.PIPE,
			    shell=True
			)
			stdout, stderr = proc.communicate()
			stdout = stdout.decode("utf-8").strip()
			stderr = stderr.decode("utf-8").strip()
			self._io.print(stdout)
			if stderr:
				self._io.print(stderr)
			if proc.returncode != 0:
				txt = f"Command exited with a return code {proc.returncode}"
				color = "yellow" if proc.returncode > 0 else "red"
				self._io.print_with_color(txt, color)

			self._io.add_to_external_shell_history(command)
			raise ShellInternalInterrupt()

	def execute(self, command):
		command = command[1:].strip()
		command = self._parse_command(command)
		if command[0].startswith("sendfile"):
			return self._sendfile(command)
		elif command[0].startswith("getfileraw"):
			return self._getfile(command)
		elif command[0].startswith("getfile"):
			return self._getfile(command)
		elif command[0].startswith("!"):
			return self._run_command()
		raise NotImplementedError("No such command")