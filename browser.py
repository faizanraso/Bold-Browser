import sys
import socket
import ssl
import tkinter, tkinter.font

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 10, 18
SCROLL_STEP = 100
FONT_SIZE = 13
view_source = False


class Browser:
    # initializing tkinter gui
    def __init__(self):
        self.window = tkinter.Tk()
        self.webpage_text = ""
        self.scroll = 0
        self.bi_times = tkinter.font.Font(
            family="Verdana",
            size=16,
        )
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.mousewheelscroll)
        self.window.bind("<Configure>", self.resizescreen)
        self.window.bind("<+>", self.zoomin)
        self.window.bind("<_>", self.zoomout)
        self.canvas = tkinter.Canvas(
            self.window,
            height=HEIGHT,
            width=WIDTH
        )

        self.canvas.pack(fill=tkinter.BOTH, expand=True)

    # functions to allow scrolling
    def scrolldown(self, e):
        if self.scroll < int(self.display_list[len(self.display_list)-1][1]) - (HEIGHT):
            self.scroll += SCROLL_STEP
            self.draw()

    def scrollup(self, e):
        if self.scroll >= SCROLL_STEP:
            self.scroll -= SCROLL_STEP
            self.draw()

    def mousewheelscroll(self, e):
        if(e.delta == -1 or e.delta == -120):
            self.scrolldown(self)
        if(e.delta == 1 or e.delta == 120):
            self.scrollup(self)

    # function to resize canvas on window size change
    def resizescreen(self, e):
        global HEIGHT, WIDTH
        HEIGHT, WIDTH = self.window.winfo_height(), self.window.winfo_width()
        self.canvas.config(height=HEIGHT, width=WIDTH)
        # self.canvas.pack(fill=tkinter.BOTH, expand=True)
        self.display_list = layout(text=self.webpage_text)
        self.draw()

    # zoom in on + press
    def zoomin(self, e):
        global HSTEP, VSTEP, FONT_SIZE
        HSTEP, VSTEP = HSTEP*1.2, VSTEP*1.2 
        FONT_SIZE *= 1.2
        self.display_list = layout(text=self.webpage_text)
        self.draw()
    
    # zoom out on - press
    def zoomout(self, e):
        global HSTEP, VSTEP, FONT_SIZE
        HSTEP, VSTEP = HSTEP/1.2, VSTEP/1.2 
        FONT_SIZE /= 1.2
        self.display_list = layout(text=self.webpage_text)
        self.draw()

    def load(self, url):
        headers, body = request(url)
        text = lex(body)
        self.webpage_text = text
        self.display_list = layout(text=text)
        self.draw()

    # draw to page
    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            # if text is not within frame, do not render
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue # y + VSTEP so that characters that are half in frame are still visble
            # else render
            self.canvas.create_text(x, y-self.scroll, text=c, font=self.bi_times, anchor='nw')

# generate layout of page (where text goes)
def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        if c == "\n":
            cursor_x = HSTEP
            cursor_y += (VSTEP)
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= (WIDTH - HSTEP):
            cursor_x = HSTEP
            cursor_y += VSTEP

    return display_list


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
    s.send("GET {} HTTP/1.0\r\n".format(path).encode("utf8") +
           "Host: {} \r\n\r\n".format(host).encode("utf8"))
    response = s.makefile("r", encoding="utf8", newline="\r\n")

    # split response
    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", "{}:{}".format(status, explanation)

    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()  # removes whitespaces

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

    # when in view source mode, display everything, including tags
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

# encryp https connection
def encryptConnection(s, host):
    ctx = ssl.create_default_context()
    return ctx.wrap_socket(s, server_hostname=host)


if __name__ == "__main__":
    browser = Browser()
    # Browser.load(sys.argv[1])
    # Browser.load(browser, "http://example.org/")
    Browser.load(browser, "https://browser.engineering/graphics.html")
    tkinter.mainloop()
