from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from threading import Timer

session = PromptSession()



t = Timer(5, cb)
t.start()

while True:
    text = session.prompt('> ', 
    	auto_suggest=AutoSuggestFromHistory(),
    )
    print('You said: %s' % text)

