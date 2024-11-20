"""GUI functionality for the browser."""

import tkinter
from url import URL

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18


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
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        cursor_x += HSTEP
        # Wrap if needed
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP

        display_list.append((cursor_x, cursor_y, c))

    return display_list


class Browser:
    """Browser GUI."""

    def __init__(self):
        """Initialise the browser window."""
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()

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
            self.canvas.create_text(x, y, text=c)

if __name__ == "__main__":
    import sys

    browser = Browser()
    url = URL(sys.argv[1])
    browser.load(url)
    browser.window.mainloop()
