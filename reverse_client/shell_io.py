#!/usr/bin/env python
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import CompleteStyle, prompt, clear
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.shell import BashLexer
from prompt_toolkit import HTML, ANSI#, print_formatted_text
from prompt_toolkit.output.color_depth import ColorDepth
from prompt_toolkit.styles import Style
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
import logging
from .print_formatted_text import print_formatted_text
from .utils import tokenize, html_escape_decorator
from .internal_commands import available_commands
from .exceptions import ShellException, ShellInternalInterrupt
from .autocompleters import InternalCommandsCompleter, ShellAutocompleter

styles_dict = {
    'blue': '#2880fc',
    'green': '#46cfb8',
    'yellow': '#d68617',
    'red': '#d61717',
    'debug': '#2880fc',
    'info': '#46cfb8',
    'warning': '#d68617 bold',
    'error': '#d61717 bold underline',
}

text_styles = Style.from_dict(styles_dict)



class ShellIO():

    def __init__(self, log_level):

        self._log_level = log_level
        shell_history = InMemoryHistory()
        self._shell_history = shell_history
        external_shell_history = InMemoryHistory()
        self._external_shell_history = external_shell_history

        self._shell_session = PromptSession(
            history=shell_history,
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            completer=InternalCommandsCompleter(),
            lexer=PygmentsLexer(BashLexer),
            complete_style=CompleteStyle.READLINE_LIKE,
            color_depth=ColorDepth.TRUE_COLOR
        )

        self._external_shell_session = PromptSession(
            history=external_shell_history,
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            completer=ShellAutocompleter(),
            lexer=PygmentsLexer(BashLexer),
            complete_style=CompleteStyle.READLINE_LIKE,
            color_depth=ColorDepth.TRUE_COLOR
        )

        self._bindings = self._get_bindings()


    def _get_bindings(self):
        bindings = KeyBindings()
        @bindings.add('c-t')
        def _(event):
            event.app.exit(":!")
        return bindings

    def _add_to_history(self, txts, history):
        for txt in txts:
            history.append_string(txt)

    def add_to_shell_history(self, txt):
        txts = tokenize("&&", ";", " ")("\\")(txt)
        txts = filter(lambda txt: txt, txts)
        txts = map(lambda txt: txt.replace(" ", "\\ "), txts)

        self._add_to_history(txts, self._shell_history)

    def add_to_external_shell_history(self, txt):
        txts = tokenize("&&", ";", " ")("\\")(txt)
        txts = filter(lambda txt: txt, txts)
        txts = map(lambda txt: txt.replace("&&", "\\&&"), txts)
        txts = map(lambda txt: txt.replace(";", "\\;"), txts)
        txts = map(lambda txt: txt.replace(" ", "\\ "), txts)

        self._add_to_history(txts, self._external_shell_history)

    def shell_input(self, txt, save_history=True, valid_input=None):
        
        try:
            with patch_stdout():
                inpt = self._shell_session.prompt(txt, key_bindings=self._bindings)
        except EOFError:
            raise KeyboardInterrupt()
        valid = valid_input is None or inpt.lower() in map(lambda x: x.lower(), valid_input)
        if not valid:
            return self.shell_input(txt, save_history, valid_input)
        return inpt

    def external_shell_input(self, txt, save_history=True):
        try:
            with patch_stdout():
                return self._external_shell_session.prompt(txt)
        except EOFError:
            raise KeyboardInterrupt
    
    def clear(self):
        clear()

    def input_text_color(self, txt, color=None):
        if color not in styles_dict:
                return [("", txt)]
        return [(styles_dict[color], txt)]

    def text_with_ansi(self, txt):
        return ANSI(txt)

    @html_escape_decorator
    def print(self, txt):
        print_formatted_text(HTML(txt), style=text_styles)

    @html_escape_decorator
    def print_with_color(self, txt, color):
        txt = HTML(f"<{color}>{txt}</{color}>")
        print_formatted_text(txt, style=text_styles)

    # <aaa fg="ansiwhite" bg="ansigreen">White on green</aaa>
    @classmethod
    @html_escape_decorator
    def debug(self, txt):
        if not isinstance(self, ShellIO): pass
        elif self._log_level > logging.DEBUG:
            return
        txt = HTML(f"<debug>{txt}</debug>")
        print_formatted_text(txt, style=text_styles)
    
    @classmethod
    @html_escape_decorator
    def info(self, txt):
        if not isinstance(self, ShellIO): pass
        elif self._log_level > logging.INFO:
            return
        txt = HTML(f"<info>{txt}</info>")
        print_formatted_text(txt, style=text_styles)
    
    @classmethod
    @html_escape_decorator
    def warning(self, txt):
        if not isinstance(self, ShellIO): pass
        elif self._log_level > logging.WARNING:
            return
        txt = HTML(f"<warning>{txt}</warning>")
        print_formatted_text(txt, style=text_styles)
    
    @classmethod
    @html_escape_decorator
    def error(self, txt):
        if not isinstance(self, ShellIO): pass
        elif self._log_level > logging.ERROR:
            return
        txt = HTML(f"<error>{txt}</error>")
        print_formatted_text(txt, style=text_styles)

