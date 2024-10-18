"""Rudiamentary libraries for displaying html content."""

from url import URL


def show(body: str):
    """Given HTML content, show eveything that is not a tag."""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")


def load(url: URL):
    """Make a http reqest and display the content."""
    body = url.request()
    show(body)


if __name__ == "__main__":
    import sys
    url = URL(sys.argv[1])
    load(url)
