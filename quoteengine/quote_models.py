"""Classes for varying quote data models. Currently only 1 is needed."""

class QuoteModel:
    """Class to encapsulate "body" and "author" for a parsed quote."""

    def __init__(self, body: str, author: str):
        """Each "quote" is comprised of two items.

        The body and the name of the author.
        Both items are passed as params whe initializing the class.

        :param body: Text of a quote, aka the quote itself.
        :param author: Name of the author of the quote.
        """
        self.body = body
        self.author = author

    def __repr__(self):
        """Retun a string representation of the quote."""
        return f'"{self.body}" - {self.author}'


