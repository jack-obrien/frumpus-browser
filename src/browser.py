"""GUI functionality for the browser."""

import tkinter
import tkinter.font
from url import URL

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100


def lex(body: str) -> str:
    """Given HTML content, return eveything that is not a tag."""
    in_tag = False
    output_text = ""
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            output_text += c

    return output_text


def layout(text) -> list[tuple[int | str]]:
    """Create a display list corresponding to text, in page coordinates.

    Returns a list of (x, y, c) for each character in text.
    """
    font = tkinter.font.Font()

    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for word in text.split():
        w = font.measure(word)
        # Wrap if needed
        if cursor_x + w > WIDTH - HSTEP:
            cursor_y += font.metrics("linespace") * 1.25
            cursor_x = HSTEP

        display_list.append((cursor_x, cursor_y, word))
        cursor_x += w + font.measure(" ")

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
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT or y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, anchor="nw")

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
