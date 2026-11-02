import http.client
import http.client
import socket
import ssl

def connection(host, timeout=90):
    return http.client.HTTPSConnection(host, port=443, timeout=timeout)


def filtered_headers(headers, excluded):
    excluded = {item.lower() for item in excluded}
    return {name: value for name, value in headers.items()
            if name.lower() not in excluded}

class DirectHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, ip, timeout=90, context=None):
        super().__init__(
            host,
            timeout=timeout,
            context=context or ssl.create_default_context(),
        )
        self.ip = ip

    def connect(self):
        raw_sock = socket.create_connection(
            (self.ip, self.port),
            self.timeout,
            self.source_address,
        )
        self.sock = self._context.wrap_socket(
            raw_sock,
            server_hostname=self.host,
        )