# Run the proxy server and open a browser to http://localhost:8080/100
import socket
import threading
import re

def handle_proxy_client(client_socket):
    try:
        # Receive the HTTP request from the client
        request = client_socket.recv(1024).decode()
        print(f"Proxy received request:\n{request}")

        # Extract the URL and validate the request
        request_line = request.split("\n")[0]

        match = re.match(r"GET http://[^/]+(/.*) HTTP/1\.", request_line)
        #if not match:
        #    send_error(client_socket, 400, "Bad Request")
        #    return

        url = match.group(1)
        if int(url.strip('/')) > 9999:
            send_error(client_socket, 414, "Request-URL Too Long")
            return

        # Forward the request to the HTTP server
        forward_request_to_server(client_socket, url)
    except Exception as e:
        print(f"Error in proxy: {e}")
    finally:
        client_socket.close()


def start_proxy(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(5)
    print(f"Proxy Server is listening on port {port}...")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Proxy accepted connection from {client_address}")
        thread = threading.Thread(target=handle_proxy_client, args=(client_socket,))
        thread.start()


def forward_request_to_server(client_socket, uri):
    try:
        # Connect to the HTTP server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect(("localhost", 8080))

        # Send the request to the HTTP server
        server_request = f"GET {uri} HTTP/1.0\r\nHost: localhost\r\n\r\n"
        server_socket.sendall(server_request.encode())

        # Receive the response from the HTTP server
        while True:
            server_response = server_socket.recv(1024)
            if not server_response:
                break
            client_socket.sendall(server_response)
    except Exception as e:
        print(f"Error while forwarding: {e}")
        send_error(client_socket, 404, "Not Found")
    finally:
        server_socket.close()


def send_error(client_socket, status_code, message):
    response = (
        f"HTTP/1.1 {status_code} {message}\r\n"
        "Content-Type: text/html\r\n"
        "Content-Length: 0\r\n"
        "\r\n"
    )
    client_socket.sendall(response.encode())


if __name__ == "__main__":
    start_proxy(8888)
