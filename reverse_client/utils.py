from functools import reduce
import re
import argparse
from prompt_toolkit.formatted_text.html import html_escape

url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))'
        # r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

ip_regex = re.compile(r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$')

socket_regex = re.compile(
    r'^socket://'
    r'(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])'
    r'(:[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])'
    r'$',
    re.IGNORECASE
)

def get_ip_port(uri):
    ip_port = uri.split("//")[-1]
    ip, port = ip_port.split(":")
    port = int(port)
    return ip, port



def get_logging_level_number(name):
    return {
        "NOTSET": 0,
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }.get(name, -1)


def html_escape_decorator(func):
    def _f(s, txt, *args, **kwargs):
        txt = html_escape(txt)
        return func(s, txt, *args, **kwargs)
    return _f


class Namespace(argparse.Namespace):
        def __init__(self, **kwargs):
            kwargs = {
                k.replace("-", "_"): v for k, v in kwargs.items()
            }
            super(Namespace, self).__init__(**kwargs)

        def __getattribute__(self, attr):
            try:
                return object.__getattribute__(self, attr)
            except:
                return None

# https://rosettacode.org/wiki/Tokenize_a_string_with_escaping#Python
def tokenize(*delims):

    def go(s, escs):
        t = ""
        res = []
        delims_esc_delims = []
        for delim in delims:
            tmp = []
            for esc in escs:
                tmp.append(esc + delim)
            delims_esc_delims.append((delim, tmp))
        
        delims_esc_delims = sorted(
            delims_esc_delims, reverse=True, 
            key=lambda t: len(t[1])
        )

        for c in s:
            t += c
            for delim, esc_delims in delims_esc_delims:
                ends_with_esc_delim = list(map(
                    lambda esc_delim: t.endswith(esc_delim),
                    esc_delims
                ))

                any_ends_with_esc_delim = any(ends_with_esc_delim)
                if t.endswith(delim) and not any_ends_with_esc_delim:
                    res.append(t[:-len(delim)])
                    t = ""
        res.append(t)
        return res

    return lambda *esc: lambda s: go(s, esc)