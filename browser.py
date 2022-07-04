import sys
import socket
import ssl
import tkinter
from tkinter.messagebox import YES
WIDTH, HEIGHT = 800, 600

view_source = False

class Browser:
    # initializing tkinter gui
    def __init__(self): 
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            height=HEIGHT,
            width=WIDTH
        )
        self.canvas.pack()
    
    def load(self, url):
        headers, body = request(url)
        text = lex(body)

        HSTEP, VSTEP = 10, 18
        cursor_x, cursor_y = HSTEP, VSTEP
        for c in text:
            self.canvas.create_text(cursor_x, cursor_y, text=c)
            
            # changing placement of where text will be generated
            cursor_x += HSTEP
            if cursor_x > (WIDTH-HSTEP):
                cursor_x = HSTEP
                cursor_y += VSTEP

def request(url):

    # check if url entered is in view-source mode
    if url.startswith("view-source"):
        url = url[len("view-source:"):]
        global view_source 
        view_source = True

    # checking if url is valid
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https"], \
        "Unknown Scheme {}".format(scheme)

    host, path = url.split("/", 1)
    path = "/" + path

    # create a socket
    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP
    )

    port = 80 if scheme == "http" else 443

    # if website uses hhtps, use ssl to encrypt the connection
    if scheme == "https":
        s = encryptConnection(s=s, host=host)

    # if a custom port was defined, extract it from host
    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    s.connect((host, port))
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

    headers["connection"] = "close"
    headers["user-agent"] = "user-agent-header"

    # these will only be found when the data is sent in an unusual way
    assert "trasnfer-encoding" not in headers
    assert "content-encoding" not in headers

    # save the rest of the response as body, and replace &gt and &lt with operand symbol
    body = response.read()
    body = body.replace("&gt;", ">")
    body = body.replace("&lt;", "<")
    s.close()

    return headers, body

def lex(body):

    # printing all text in body (excludes HTML tags and styles)
    in_angle = False
    number_of_close_braces = body.count("}")
    number_of_braces_count = 0
    text = ""

    #when in view source mode, display everything, including tags
    if view_source: 
        for c in body:
            text += c
    else:
        for c in body:
            if c == "<":
                in_angle = True
            elif c == ">":
                in_angle = False
            elif c == "}":
                number_of_braces_count += 1
            elif not in_angle and number_of_braces_count == number_of_close_braces:
                text += c
    return text

def encryptConnection(s, host):
    ctx = ssl.create_default_context()
    return ctx.wrap_socket(s, server_hostname=host)


if __name__ == "__main__":
    browser = Browser()
    # Browser.load(sys.argv[1])
    # Browser.load(browser, "http://example.org/")
    Browser.load(browser, "https://www.zggdwx.com/xiyou/1.html")
    tkinter.mainloop()
