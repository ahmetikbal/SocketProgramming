# Run the server (python http_server.py <port>) and open a browser to http://localhost:8080/100
import socket
import threading
import re
import sys

def handle_client(client_socket):
    try:
        # Receive the HTTP request from the client
        request = client_socket.recv(1024).decode()
        print(f"Request received:\n{request}")

        # Extract the first line of the request (e.g., "GET /500 HTTP/1.1")
        request_line = request.split("\n")[0]

        # Only handle GET requests
        if not request_line.startswith("GET"):
            send_error(client_socket, 501, "Not Implemented")
            return

        # Extract the URI and validate its size
        match = re.match(r"GET /(\d+) HTTP/1\.", request_line)
        if not match:
            send_error(client_socket, 400, "Bad Request")
            return

        size = int(match.group(1))
        if size < 100 or size > 20000:
            send_error(client_socket, 400, "Bad Request")
            return

        # Generate the HTML document and send the response
        html_content = generate_html(size)
        if html_content is None:
            send_error(client_socket, 400, "Bad Request")
            return

        send_response(client_socket, html_content)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def start_server(port):
    # Create a server socket to listen for incoming connections
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(5)
    print(f"HTTP Server is listening on port {port}...")

    while True:
        # Accept new client connections
        client_socket, client_address = server_socket.accept()
        print(f"Connection accepted from {client_address}")

        # Start a new thread for each client
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

def generate_html(size):
    # Fixed parts of the HTML structure
    base_html = "<HTML> <HEAD> <TITLE>I am {} bytes long</TITLE> </HEAD> <BODY>".format(size)
    closing_html = "</BODY> </HTML>"

    # Calculate remaining content size and fill it
    content_length = size - len(base_html) - len(closing_html) - 1
    if content_length < 0:
        return None

    filler = "a " * (content_length // 2)  # 2 bytes for each a
    if content_length % 2 == 1:
        filler += "a"  # If the odd number, add an extra "a"

    return f"{base_html} {filler.strip()} {closing_html}"

def send_response(client_socket, html_content):
    # Calculate the size of the HTML content
    content_length = len(html_content.encode('utf-8'))

    # Construct the HTTP response with headers and content
    response_headers = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html\r\n"
        f"Content-Length: {content_length}\r\n"
        "\r\n"  # Blank line separating headers and body
    )
    response = response_headers + html_content

    # Send the response back to the client
    client_socket.sendall(response.encode('utf-8'))

def send_error(client_socket, status_code, message):
    # Construct an error response
    response = (
        f"HTTP/1.1 {status_code} {message}\r\n"
        "Content-Type: text/html\r\n"
        "Content-Length: 0\r\n"
        "\r\n"
    )
    # Send the error response to the client
    client_socket.sendall(response.encode())

if __name__ == "__main__":
    # Ensure a port number is provided as a command-line argument
    if len(sys.argv) != 2:
        print("Usage: python http_server.py <port>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        if port < 1 or port > 65535:
            raise ValueError
    except ValueError:
        print("Error: Port number must be an integer between 1 and 65535.")
        sys.exit(1)

    # Extract the port number and start the server
    port = int(sys.argv[1])
    start_server(port)
