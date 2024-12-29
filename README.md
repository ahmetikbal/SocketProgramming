The project aims to simulate a client-server model with both an HTTP server and a Proxy server. The HTTP server generates dynamic content based on the size specified in the URL, while the Proxy server forwards client requests to the HTTP server and implements caching. The Proxy Server listens on a fixed port (8888), processes incoming client requests, checks the URL length, and either serves cached content or forwards the request to the HTTP server. The HTTP Server listens on a configurable port, processes GET requests, generates HTML content dynamically based on the size in the URL, and responds to the Proxy server.

![image](https://github.com/user-attachments/assets/1013e411-7e31-4fae-ba1b-5e779785badc)

1- Run the server (python http_server.py <port>) and open a browser to http://localhost:8080/100 

2- Run the proxy server (python http_server.py) and open a browser to http://localhost:8080/100 (proxy server listens on port 8888)
