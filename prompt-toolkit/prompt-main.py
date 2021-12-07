#!/usr/bin/env python
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import CompleteStyle, prompt
from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.shell import BashLexer
from functools import reduce
from threading import Timer


# from prompt_toolkit.completion import FuzzyCompleter
# import click
internal_commands = ["sendfile", "getfile", "getfileraw"]


class InternalCommandsCompleter(Completer):

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        text = document.text.lstrip()
        if not text or text[0] != ":":
            return
        text = text.split(" ")
        if len(text) != 1:
            return
        text = text[0][1:].strip()
        for cmd in internal_commands:
            if not cmd.startswith(text):
                continue
            yield Completion(":" + cmd, start_position=-len(word_before_cursor))

def main():
    # Create some history first. (Easy for testing.)
    history = InMemoryHistory()
    # history.append_string("import path")
    
    # completer = WordCompleter(['select', 'from', 'insert', 'update', 'delete', 'drop'], ignore_case=True)

    session = PromptSession(
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=True,
        completer=InternalCommandsCompleter(),
        lexer=PygmentsLexer(BashLexer),
        complete_style=CompleteStyle.MULTI_COLUMN,
    )
    while True:
        try:
            text = session.prompt("Say something: ")
            print(text)
            for t in tokenize(" ")("\\")(text.strip()):
                if not t:
                    continue
                # print(t)
                history.append_string(t.replace(" ", "\\ "))
            # click.echo_via_pager(text)
        except KeyboardInterrupt:
            return
        except Exception:
            return
    # print("You said: %s" % text)


if __name__ == "__main__":
    main()
