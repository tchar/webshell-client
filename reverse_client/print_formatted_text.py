from threading import main_thread, current_thread
from asyncio import get_event_loop
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit import print_formatted_text as original_print_formatted_text

class _ThreadCtx():
    loop = get_event_loop()

def print_formatted_text(*args, **kwargs):

    loop = _ThreadCtx.loop

    def _print_formatted_text():
        original_print_formatted_text(*args, **kwargs)

    def _run_in_terminal():
        run_in_terminal(_print_formatted_text, in_executor=False)

    if main_thread() == current_thread():
        _print_formatted_text()
    else:
        loop.call_soon_threadsafe(_run_in_terminal)