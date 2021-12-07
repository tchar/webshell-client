import os
# from pathlib import PosixPath
from prompt_toolkit.completion import Completer, Completion, NestedCompleter
from .utils import tokenize
from .internal_commands import available_commands
from .exceptions import ShellException


class FileAutoCompleter(Completer):
    def get_completions(self, document, complete_event, search):

        expanded_search = os.path.expanduser(search)

        if os.path.isdir(expanded_search):
            search_dir = search
            expanded_search_dir, search_fname = expanded_search, ""
        else:
            search_dir = os.path.dirname(search)
            expanded_search_dir, search_fname = os.path.split(expanded_search)

        try:
            dirs = os.listdir(expanded_search_dir)
        except:
            return

        for completion in dirs:
            if not completion.startswith(search_fname):
                continue
            completion = os.path.join(search_dir, completion)
            completion = completion + os.path.sep if os.path.isdir(completion) else completion
            yield Completion(completion, start_position=-len(search))


class ShellAutocompleter(Completer):
    def __init__(self):
        super(ShellAutocompleter, self).__init__()
        self._file_autocompleter = FileAutoCompleter()

    @classmethod
    def _should_autocomplete_env(cls, txt):
        txt = txt.lstrip()
        txt = tokenize("&&", ";")("\\")(txt)
        last_txt = txt[-1]
        last_txt = last_txt.lstrip()
        last_txt = tokenize(" ")("\\")(last_txt)
        return len(last_txt) == 1


    def get_completions(self, document, complete_event):
        
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        word_before_cursor = tokenize(";", "&&", " ")("\\")(word_before_cursor)
        word_before_cursor = word_before_cursor[-1]

        for item in self._file_autocompleter.get_completions(document, complete_event, word_before_cursor):
            yield item
 
        if not ShellAutocompleter._should_autocomplete_env(document.text):
            return


        autocompleted_envs = set()

        env_paths = os.environ["PATH"]
        env_paths = env_paths.split(":")

        for env_path in env_paths:
            if not os.path.isdir(env_path):
                continue
            for filename in os.listdir(env_path):
                if not filename.startswith(word_before_cursor):
                    continue
                filepath = os.path.join(env_path, filename)
                if not os.access(filepath, os.X_OK):
                    continue
                if filename in autocompleted_envs:
                    continue
                autocompleted_envs.add(filename)
                yield Completion(filename, start_position=-len(word_before_cursor))

       


class InternalCommandsCompleter(Completer):

    def __init__(self):
        super(InternalCommandsCompleter, self).__init__()
        self._file_autocompleter = FileAutoCompleter()
        ## Load internal commands

    def _main_autocompleter(self, document, complete_event, commands):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        command = commands[0][1:].strip()
        for cmd in available_commands:
            if not cmd.startswith(command):
                continue
            yield Completion(":" + cmd + " ", start_position=-len(word_before_cursor))

    def _getfile_completer(self, document, complete_event, commands):        
        commands = filter(lambda t: t.strip() != "", commands)
        commands = list(commands)

        if len(commands) != 3:
            return

        search = commands[2]
        for item in self._file_autocompleter.get_completions(document, complete_event, search):
            yield item

    def _sendfile_completer(self, document, complete_event, commands):
        
        commands = filter(lambda t: t.strip() != "", commands)
        commands = list(commands)

        if len(commands) != 2:
            return

        search = commands[1]
        for item in self._file_autocompleter.get_completions(document, complete_event, search):
            yield item

    def get_completions(self, document, complete_event):
        text = document.text.lstrip()
        if not text or text[0] != ":":
            return
        text = tokenize(" ")("\\")(text)
        text = map(lambda t: t.replace(" ", "\\ "), text)
        text = list(text)
        
        if len(text) == 0:
            return

        completer = None
        if len(text) != 1:
            if text[0] in [":getfile", ":getfileraw"]:
                completer = self._getfile_completer(document, complete_event, text)
            elif text[0] == ":sendfile":
                completer = self._sendfile_completer(document, complete_event, text)
            else:
                return
        else:
            completer = self._main_autocompleter(document, complete_event, text)
        
        for item in completer:
            yield item