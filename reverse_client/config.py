import os
import argparse
import configparser
import logging
from .utils import url_regex, socket_regex, ip_regex, Namespace, get_logging_level_number

def parse_config():
	config = configparser.ConfigParser()

	if not os.path.isfile("config.ini"):
		print("config.ini does not exist, will read from command line arguments")
		return Namespace(), []

	config.read("config.ini")
	args = {}
	cli_args = []
	for section in config:
		for arg, value in config.items(section):
			# args[arg.replace("-", "_")] = value
			args[arg] = value
			arg = f"--{arg}"
			cli_args.append(arg)
			cli_args.append(value)
	return Namespace(**args), cli_args


def get_config():

	def _uri_type(arg):
		if not url_regex.match(arg) and not socket_regex.match(arg):
			raise argparse.ArgumentTypeError(f"{arg} is not a valid uri")
		return arg

	def _ip_type(arg):
		if not ip_regex.match(arg):
			raise argparse.ArgumentTypeError(f"{arg} is not an ip")
		return arg

	def _ip_port_type(arg):
		tmp = arg.split(":")
		error_msg = f"{arg} is an invalid IP:PORT address"
		if len(tmp) != 2:
			raise argparse.ArgumentTypeError(error_msg)
		
		ip, port = tmp
		ip = _ip_type(ip)
		port = _number_type(int, 1, 65535)(port)

		return arg

	def _required_str_type(arg):
		if arg is None or arg.strip() == "":
			raise argparse.ArgumentTypeError(f"{arg} is empty")
		return arg

	def _number_type(n_type, minimum=None, maximum=None):
		def _f(arg):
			try:
				arg = n_type(arg)
			except ValueError:
				raise argparse.ArgumentTypeError(f"{arg} is not of type '{n_type.__name__}'")
			if minimum is not None and arg < minimum:
				raise argparse.ArgumentTypeError(f"{arg} is less than the minimum of {minimum}")
			if maximum is not None and arg > maximum:
				raise argparse.ArgumentTypeError(f"{arg} is more than the maximum of {maximum}")
			return arg
		return _f




	argparser = argparse.ArgumentParser()
	args, cli_args = parse_config()

	group = argparser.add_mutually_exclusive_group(
		required="listen" not in args and "uri" not in args
	)

	group.add_argument(
		"-l",
		"--listen",
		type=_ip_port_type,
		default=args.listen
	)
	group.add_argument(
		"-u",
		"--uri",
		type=_uri_type,
		default=args.uri
	)
	argparser.add_argument(
		"--method",
		choices=["post", "get"],
		default=args.method or "post"
	)
	argparser.add_argument(
		"--post-body-format",
		choices=["x-www-uriencoded", "json"],
		default=args.post_body_format or "json"
	)
	argparser.add_argument(
		"--command-key",
		type=_required_str_type,
		default=args.command_key
	)
	argparser.add_argument(
		"-t",
		"--token",
		default=args.token
	)
	argparser.add_argument(
		"--token-key",
		default=args.token_key
	)
	argparser.add_argument(
		"--virtual",
		choices=["on", "off", "force"],
		default=args.virtual or "off"
	)
	argparser.add_argument(
		"--last-line",
		choices=["command", "command-result"],
		default=args.last_line or "command"
	)
	argparser.add_argument(
		"--log-level",
		choices=["notset", "debug", "info", "warning", "error"],
		default=args.log_level or "warning"
	)
	argparser.add_argument(
		"--connection-controller",
		choices=[
			"default-requests",
			"tor-requests",
			"socket-client"
		],
		default=args.connection_controller or "default_requests_controller"
	)
	argparser.add_argument(
		"--tor-ip",
		type=_ip_type, 
		default=args.tor_ip
	)
	argparser.add_argument(
		"--tor-port",
		type=_number_type(int, minimum=1, maximum=65535), 
		default=args.tor_port
	)
	argparser.add_argument(
		"--tor-control-port",
		type=_number_type(int, minimum=1, maximum=65535), 
		default=args.tor_control_port
	)
	argparser.add_argument(
		"--tor-control-password",
		default=args.tor_control_password
	)
	argparser.add_argument(
		"--tor-refresh-ip-every",
		type=_number_type(float, minimum=1, maximum=None), 
		default=args.tor_refresh_ip_every
	)
	argparser.add_argument(
		"--tor-ensure-ip-change",
		type=bool,
		default=args.tor_ensure_ip_change or False
	)

	argparser.parse_args(cli_args)

	args = argparser.parse_args()

	if (args.connection_controller in ["default_requests", "tor_requests"] and
		not url_regex.match(args.uri)):
		argparser.error("argument --uri: Not a url")

	if (args.connection_controller in ["socket_client"] and
		not socket_regex.match(args.uri)):
		argparser.error("argument --uri: Not a socket uri")

	if args.token is not None and args.token_key is None:
		argparser.error("argument --token: requires --token-key, define it in config.ini or as a command line argument")

	args.log_level = get_logging_level_number(args.log_level.upper())

	return args