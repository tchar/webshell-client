import logging
from reverse_client.shell import Shell
from reverse_client.shell_io import ShellIO
from reverse_client.connection_controller import ConnectionControllerFactory
from reverse_client.internal_commands import InternalCommands
from reverse_client.config import get_config

def main():
	config = get_config()

	io = ShellIO(config.log_level)

	connection_controller = ConnectionControllerFactory.get_connection_controller(
		config.connection_controller,
		uri=config.uri,
		shell_io=io,
		method=config.method,
		post_body_format=config.post_body_format,
		command_key=config.command_key,
		token=config.token,
		token_key=config.token_key,
		tor_ip=config.tor_ip,
		tor_port=config.tor_port,
		tor_control_port=config.tor_control_port,
		tor_control_password=config.tor_control_password,
		tor_refresh_ip_every=config.tor_refresh_ip_every
	)
	internal_commands = InternalCommands(io)

	shell = Shell(
		uri=config.uri,
		virtual=config.virtual,
		last_line=config.last_line,
		io=io,
		connection_controller=connection_controller,
		internal_commands=internal_commands
	)
	shell.start()

if __name__ == "__main__":
	main()