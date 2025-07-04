"""GUI functionality for the browser."""

import tkinter
import tkinter.font
from url import URL

WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 100
HSTEP, VSTEP = 13, 18

# Store tkinter font objects in a dictionary. The font objects automatically cache
# words to improve lookup speed, we just need to use the same font object each time
# per font.
# Keys: (size, weight, style) tuple
# Values: (tkinter.fonts.Font, tkinter.Label) tuple. For some reason the font object
#   needs to come with a tkinter label as well to improve performance?
#   yeah, the authors of the browser book dont really know why this is either.
FONT_CACHE = {}


def get_font(size, weight, style):
    """Lookup font in the global FONT_CACHE, adding it if it does not exist."""
    key = (size, weight, style)
    if key not in FONT_CACHE:
        font = tkinter.font.Font(size=size, weight=weight, slant=style)
        label = tkinter.Label(font=font)
        FONT_CACHE[key] = (font, label)
    return FONT_CACHE[key][0]


class Text:
    """Text from a leaf of the DOM tree."""

    def __init__(self, text: str, parent):
        self.text = text
        self.children = []  # Text nodes are leaves so never have children, but this
        # field is here for consistency
        self.parent = parent

    def __repr__(self):
        return repr(self.text)


class Element:
    """HTML node from the DOM with an opening and closing tag."""

    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.children = []
        self.parent = parent
        self.attributes = attributes

    def __repr__(self):
        return "<" + self.tag + ">"


def print_tree(node: Text | Element, indent=0):
    """Pretty print the HTML tree, given the root node."""
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)


class HTMLParser:
    """Parser for web HTML text which builds a tree of nodes."""

    SELF_CLOSING_TAGS = [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]

    def __init__(self, body: str):
        self.body = body
        self.unfinished_tags = []

    def parse(self):
        """Parse HTML into tags and text."""
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)

        # Here we are done with parsing the text
        return self.finish()

    def add_text(self, text):
        """Add the given text to the DOM tree as a text node."""
        if text.isspace():
            # NOTE: Handle edge case where we get /n before opening any tags.
            return

        parent = self.unfinished_tags[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def get_attributes(self, text):
        """Get the attributes of a HTML tag.

        Assumes the attributes contain no whitespace.
        """
        parts = text.split()
        tag = parts[0].casefold()  # Safer way to handle case insensitive stuff.
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                # The value might be quoted so we need to remove quotes.
                if len(value) > 2 and value[0] in ["'", '"']:
                    value = value[1:-1]
                attributes[key.casefold()] = value
            else:
                attributes[attrpair.casefold()] = ""

        return tag, attributes

    def add_tag(self, tag):
        """Add the given tag to the DOM tree as an element."""
        # Separate into tag and attributes
        tag, attributes = self.get_attributes(tag)

        if tag.startswith("!"):
            # Ignore !doctype tag and comment
            return
        if tag.startswith("/") and len(self.unfinished_tags) == 1:
            # NOTE: Handle edge case where we are last closing tag with no
            # unfinished parent.
            return
        elif tag.startswith("/"):
            # This is a closing tag. Finish the last unfinished node in the tree.
            # NOTE: This assumes no unfinished nodes within the element.
            node = self.unfinished_tags.pop()
            parent = self.unfinished_tags[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            # Add these tags to the tree without a closing tag.
            parent = self.unfinished_tags[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            # This is an opening tag - add an unfinished node to the tree.
            # NOTE: Handle edge case if the node is the first it has no parent.
            parent = self.unfinished_tags[-1] if self.unfinished_tags else None
            node = Element(tag, attributes, parent)
            self.unfinished_tags.append(node)

    def finish(self) -> Text | Element:
        """Complete the tree by finishing any unfinished nodes."""
        while len(self.unfinished_tags) > 1:
            node = self.unfinished_tags.pop()
            parent = self.unfinished_tags[-1]
            parent.children.append(node)

        return self.unfinished_tags.pop()


class Layout:
    """Layout of a webpage."""

    def __init__(self, root_node: Element | Text) -> None:
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

        self.recurse_layout(root_node)

        self.flush()

    def recurse_layout(self, node: Text | Element):
        """Layout an entire page, already parsed."""
        if isinstance(node, Text):
            for word in node.text.split():
                self.layout_word(word)
        elif isinstance(node, Element):
            self.open_tag(node)
            for child in node.children:
                self.recurse_layout(child)
            self.close_tag(node)

    def open_tag(self, tag: Element):
        """Apply the tag to self."""
        if tag.tag == "i":
            self.style = "italic"
        elif tag.tag == "b":
            self.weight = "bold"
        elif tag.tag == "small":
            self.size -= 2
        elif tag.tag == "big":
            self.size += 4
        elif tag.tag == "br":  # HTML tag for line break
            self.flush()

    def close_tag(self, tag: Element):
        """Stop applying the tag to self."""
        if tag.tag == "i":
            self.style = "roman"
        elif tag.tag == "b":
            self.weight = "normal"
        elif tag.tag == "small":
            self.size += 2
        elif tag.tag == "big":
            self.size -= 4
        elif tag.tag == "p":  # HTML tag for end of paragraph
            self.flush()
            self.cursor_y += VSTEP  # Add spacing between paragraphs

    def layout_word(self, word: Text):
        """Place token in correct place in the layout."""
        # Update font based on html tag parsing variables
        font = get_font(self.size, self.weight, self.style)

        w = font.measure(word)
        # Wrap if needed
        if self.cursor_x + w > WIDTH - HSTEP:
            self.flush()

        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")

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
        self.window.title("frumpus")
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
        self.root_node = HTMLParser(body).parse()

        # Create a display list of the text
        self.display_list = Layout(self.root_node).display_list
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
