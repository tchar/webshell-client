class RequestError(ConnectionError): pass

class TorConnectionError(ConnectionError): pass
class TorRenewConnectionError(ConnectionError): pass

class SocketConnectionError(ConnectionError): pass