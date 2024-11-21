"""GUI functionality for the browser."""

import tkinter
import tkinter.font
from url import URL

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100


class Text:
    """Text from webpage."""

    def __init__(self, text):
        self.text = text


class Tag:
    """HTML tag."""

    def __init__(self, tag):
        self.tag = tag


def lex(body: str) -> list[Tag | Text]:
    """Parse HTML into tags and text."""
    out = []
    buffer = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if buffer:
                out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        else:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out


def layout(tokens: list[Tag | Text]) -> list[tuple[int | str]]:
    """Create a display list corresponding to text, in page coordinates.

    Returns a list of (x, y, c) for each character in text.
    """
    font = tkinter.font.Font()
    weight = "normal"
    style = "roman"

    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for token in tokens:
        if isinstance(token, Text):
            for word in token.text.split():
                # Update font based on html tag parsing variables
                font = tkinter.font.Font(size=16, weight=weight, slant=style)

                w = font.measure(word)
                # Wrap if needed
                if cursor_x + w > WIDTH - HSTEP:
                    cursor_y += font.metrics("linespace") * 1.25
                    cursor_x = HSTEP

                display_list.append((cursor_x, cursor_y, word, font))
                cursor_x += w + font.measure(" ")

        elif token.tag == "i":
            style = "italic"
        elif token.tag == "/i":
            style = "roman"
        elif token.tag == "b":
            weight = "bold"
        elif token.tag == "/b":
            weight = "normal"

    return display_list


class Browser:
    """Browser GUI."""

    def __init__(self):
        """Initialise the browser window."""
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.scroll = 0  # Offset between page coords and screen coords.
        self.canvas.pack()

        # Scrolling
        self.window.bind("<Down>", self.scrolldown)

    def load(self, url: URL):
        """Make a http reqest and display the content."""
        # Make http request.
        body = url.request()

        # Convert HTML into plain text
        text = lex(body)

        # Create a display list of the text
        self.display_list = layout(text)
        self.draw()

    def draw(self) -> None:
        """Render text character by character."""
        for x, y, c, font in self.display_list:
            if y > self.scroll + HEIGHT or y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, anchor="nw", font=font)

    def scrolldown(self, e) -> None:
        """Scroll the displayed text down.

        The argument e is an igored tkinter event.
        """
        self.scroll += SCROLL_STEP
        self.canvas.delete("all")
        self.draw()


if __name__ == "__main__":
    import sys

    browser = Browser()
    url = URL(sys.argv[1])
    browser.load(url)
    browser.window.mainloop()
