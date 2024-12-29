# Run the proxy server and open a browser to http://localhost:8080/100
import socket
import threading
import re
import os
import time
import hashlib

# Cache Directory Configuration
CACHE_DIR = "cache"
CACHE_SIZE_LIMIT = 20  #limit for the number of files in the cache directory

# Create cache directory if it doesn't exist
if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)


def get_cache_filename(url):
    """ Converts the URL to a cache file """
    return os.path.join(CACHE_DIR, hashlib.md5(url.encode()).hexdigest())


def is_cache_valid(cache_filename):
    """ Checks whether the cache is valid """
    if not os.path.exists(cache_filename):
        return False
    # Check if the cache is still valid (e.g., 1 day)
    cache_time = os.path.getmtime(cache_filename)
    current_time = time.time()
    # Valid for 1 day (86400 seconds)
    if current_time - cache_time < 86400:
        return True
    return False


def get_from_cache(url):
    """ Retrieves the data from the cache """
    cache_filename = get_cache_filename(url)
    if is_cache_valid(cache_filename):
        with open(cache_filename, 'rb') as f:
            return f.read()
    return None


def save_to_cache(url, data):
    """ Saves the data to the cache """
    cache_filename = get_cache_filename(url)
    with open(cache_filename, 'wb') as f:
        f.write(data)
    # If the cache capacity is exceeded, delete the oldest file using FIFO
    clean_cache()


def clean_cache():
    """ Cleans up the cache (FIFO) """
    cache_files = sorted(
        [os.path.join(CACHE_DIR, f) for f in os.listdir(CACHE_DIR)],
        key=os.path.getmtime
    )
    if len(cache_files) > CACHE_SIZE_LIMIT:
        os.remove(cache_files[0])  # The oldest file is removed


def get_conditional_headers(url):
    """ Adds conditional GET headers based on the file length """
    cache_filename = get_cache_filename(url)
    if os.path.exists(cache_filename):
        file_length = os.path.getsize(cache_filename)
        if file_length % 2 == 1:  # If the file length is odd, assume it has not changed
            return {"If-Modified-Since": time.ctime()}
    return {}


def forward_request_to_server(client_socket, url, port):
    try:
        # Connect to the HTTP server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect(("localhost", port))

        # Prepare the request headers with conditional GET
        headers = get_conditional_headers(url)
        headers_str = "\r\n".join([f"{key}: {value}" for key, value in headers.items()])

        # Send the request to the HTTP server
        server_request = f"GET {url} HTTP/1.0\r\nHost: localhost\r\n{headers_str}\r\n\r\n"
        server_socket.sendall(server_request.encode())

        # Receive the response from the HTTP server
        server_response = b""
        while True:
            data = server_socket.recv(1024)
            if not data:
                break
            server_response += data

        # Cache the response if it's a new object
        save_to_cache(url, server_response)

        # Send the response to the client
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

        # Parse port from request (default to 8080 if not specified)
        port_match = re.search(r"localhost:(\d+)", request_line)
        port = int(port_match.group(1)) if port_match else 8080

        # Check if the content is in cache
        cached_data = get_from_cache(url)
        if cached_data:
            print(f"Cache hit for {url}")
            # Send cached data to client
            client_socket.sendall(cached_data)
        else:
            print(f"Cache miss for {url}")
            forward_request_to_server(client_socket, url, port)
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


if __name__ == "__main__":
    start_proxy(8888)
