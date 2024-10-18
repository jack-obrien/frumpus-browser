"""URL Parsing."""

import socket
import ssl


class URL:
    """URL object handling parsing and HTTP requests."""

    def __init__(self, url: str):
        """Initialise a URL by parsing the string into its components."""
        self.scheme, url = url.split("://", maxsplit=1)
        assert self.scheme in ["http", "https"]

        # Set port based on http vs https
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if "/" not in url:
            self.host = url
            url = ""
        else:
            self.host, url = url.split("/", maxsplit=1)

        # Parse port number from host to replace the default port number
        if ":" in self.host:
            self.host, self.port = self.host.split(":", maxsplit=1)
            self.port = int(self.port)

        self.path = "/" + url

    def request(self):
        """Download the webpage specified by self.

        Returns: str
            web content

        """
        # Create socket connection to self.host
        host_connection_socket = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        host_connection_socket.connect((self.host, self.port))

        # If our scheme is https, wrap the socket using SSL to allow for TLS encryption
        if self.scheme == "https":
            context = ssl.create_default_context()
            host_connection_socket = context.wrap_socket(
                host_connection_socket, server_hostname=self.host
            )

        # Create HTTP request
        request = f"GET {self.path} HTTP/1.0\nHost {self.host}\n\n"
        host_connection_socket.send(request.encode("utf8"))

        # Get response as a string
        # afaik makefile is just a helper which waits for all bits to arrive from the
        # socket.
        response = host_connection_socket.makefile("r", encoding="utf8")

        # Parse the status line in the response
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", maxsplit=2)

        # Parse the headers in the response
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\n":
                break
            header, value = line.split(":", maxsplit=1)
            response_headers[header.lower()] = value.strip()

        # Ensure that some weird encodings are not present? IDK
        assert (
            "transfer-encoding" not in response_headers
            and "content-encoding" not in response_headers
        )

        # Get the web content and close the socket
        content = response.read()
        host_connection_socket.close()
        return content
