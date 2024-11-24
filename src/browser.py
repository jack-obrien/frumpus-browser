"""GUI functionality for the browser."""

import tkinter
import tkinter.font
from url import URL

WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 100
HSTEP, VSTEP = 13, 18


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


class Layout:
    """Layout of a webpage."""

    def __init__(self, tokens: list[Tag | Text]) -> None:
        """Initialise a Layout."""
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 12

        # Store the current line in memory so we can adjust word heights in a second
        # pass. This lets us adjust for different font sizes on the same line.
        self.line = []

        for token in tokens:
            self.layout_token(token)

        self.flush()

    def layout_token(self, token: Tag | Text) -> tuple[int | str | tkinter.font.Font]:
        """Place token in correct place in the layout."""
        if isinstance(token, Text):
            for word in token.text.split():
                # Update font based on html tag parsing variables
                font = tkinter.font.Font(
                    size=self.size, weight=self.weight, slant=self.style
                )

                w = font.measure(word)
                # Wrap if needed
                if self.cursor_x + w > WIDTH - HSTEP:
                    self.flush()
                    # self.cursor_y += font.metrics("linespace") * 1.25
                    # self.cursor_x = HSTEP

                self.line.append((self.cursor_x, word, font))
                self.cursor_x += w + font.measure(" ")

        elif token.tag == "i":
            self.style = "italic"
        elif token.tag == "/i":
            self.style = "roman"
        elif token.tag == "b":
            self.weight = "bold"
        elif token.tag == "/b":
            self.weight = "normal"
        elif token.tag == "small":
            self.size -= 2
        elif token.tag == "/small":
            self.size += 2
        elif token.tag == "big":
            self.size += 4
        elif token.tag == "/big":
            self.size -= 4
        elif token.tag == "br":  # HTML tag for line break
            self.flush()
        elif token.tag == "/p":  # HTML tag for end of paragraph
            self.flush()
            self.cursor_y += VSTEP  # Add spacing between paragraphs

    def flush(self):
        """Second pass of page layout after each line, to align baselines."""
        if not self.line:
            return

        # Get the max font ascent on self.line
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])

        # Move the baseline to make room for the max ascent.
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        # Move self.cursor_y down to adjust for the deepest descent
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

        self.cursor_x = HSTEP
        self.line = []


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
        tokens = lex(body)

        # Create a display list of the text
        self.display_list = Layout(tokens).display_list
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
