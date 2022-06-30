import sys
import socket
import ssl

def request(url):
    # checking if url is valid
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https"], "Unknown Scheme {}".format(scheme)

    url = url[len("http://"):]
    host, path = url.split("/", 1)
    path = "/" + path

    # create a socket
    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP
    )

    s.connect((host, 80))
    s.send("GET {} HTTP/1.0\r\n".format(path).encode("utf8") + "Host: {} \r\n\r\n".format(host).encode("utf8"))
    response = s.makefile("r", encoding="utf8", newline="\r\n")

    # split response
    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", "{}:{}".format(status, explanation)

    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n": break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip() # removes whitespaces

    # these two will only be found when the data is sent in an unusual way
    assert "trasnfer-encoding" not in headers
    assert "content-encoding" not in headers

    # save the rest of the response as body
    body = response.read()
    s.close()

    return headers, body

def show(body):
    # printing all text in body (excludes HTML tags)
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            print(c, end="")


def load(url):
    headers, body = request(url)
    show(body)

def encryptConnection(s, host):
    ctx = ssl.create_default_context()
    return ctx.wrap_socket(s, server_hostname=host)


if __name__ == "__main__":
    load(sys.argv[1])