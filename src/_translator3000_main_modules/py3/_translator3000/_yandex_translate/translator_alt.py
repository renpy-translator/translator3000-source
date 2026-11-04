from . import translator
from .. import selenium_session

class Translator(translator.Translator):
    __author__ = 'Vladya'
    LOGGER = translator.Translator.LOGGER.getChild('Alt')
    BROWSER_TRANSLATOR = True

    def _web_translate(self, text, dest, src):
        with selenium_session.lock:
            result = super(Translator, self)._web_translate(text, dest, src, _use_selenium=True)
        return result
