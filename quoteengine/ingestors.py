"""Classes used to read quotes from various file types."""
import subprocess
import tempfile
from abc import ABC
from itertools import chain
from typing import List
import re

import docx
import pandas as pd

from quoteengine import QuoteModel


class IngestorInterface(ABC):
    """Abstract base class for parsing quotes stored in varying file formats."""

    allowed_extensions = []

    @classmethod
    def can_ingest(cls, path) -> bool:
        """Return boolean if the passed path has an extension in allowed_extensions."""
        return cls.ext_from_path(path) in cls.allowed_extensions

    @classmethod
    def parse(cls, path: str) -> List[QuoteModel]:
        """Return `QuoteModels` for each quote found in a parsed file.

        This is the main override for subclass implementations.
        """
        pass

    @classmethod
    def ext_from_path(cls, path):
        """Return a file extension from path string."""
        return path.split('.')[-1]

    @classmethod
    def extension_support(cls):
        """Return a list of all supported parse extension formats from subclasses."""
        return list(chain(*[c.allowed_extensions for c in cls.__subclasses__()]))

    @classmethod
    def clean_text(cls, text):
        """Return text free of unwanted and non-printable characters."""
        remove_chars = r"[()\"#/@;<>{}`+=~|.!?,]"
        return ''.join(filter(str.isprintable, re.sub(remove_chars, "", text).strip()))


class DocxIngestor(IngestorInterface):
    """Imports quotes from docx files."""

    allowed_extensions = ['docx']

    @classmethod
    def parse(cls, path: str) -> List[QuoteModel]:
        """Return a list of `QuoteModel` from parsing docx file."""
        if not cls.can_ingest(path):
            raise ValueError(f"File Type not supported for {path}")

        doc = docx.Document(docx=path)
        return [QuoteModel(body=cls.clean_text(q.text.split("-")[0]),
                           author=cls.clean_text(q.text.split("-")[1])
                           ) for q in doc.paragraphs if q.text]


class PdfIngestor(IngestorInterface):
    """Imports quotes from pdf files using subprocess to launch pdftotext."""

    allowed_extensions = ['pdf']

    @classmethod
    def parse(cls, path: str) -> List[QuoteModel]:
        """Return a list of `QuoteModel` from parsing pdf file with pdftotext binary."""
        if not cls.can_ingest(path):
            raise ValueError(f"File Type not supported for {path}")

        tmp = tempfile.NamedTemporaryFile(suffix=".txt")
        sub_p = subprocess.run(['pdftotext', path, tmp.name], check=True)
        if sub_p.returncode:
            raise RuntimeError("Subprocess 'pdftotext' did not return successfully.")
        return TxtIngestor.parse(tmp.name)


class CsvIngestor(IngestorInterface):
    """Imports quotes from csv files using pandas read_csv."""

    allowed_extensions = ['csv']

    @classmethod
    def parse(cls, path: str) -> List[QuoteModel]:
        """Return a list of `QuoteModel` from parsing a csv file with pandas."""
        if not cls.can_ingest(path):
            raise ValueError(f"File Type not supported for {path}")
        return pd.read_csv(path).apply(lambda x: QuoteModel(body=x.body, author=x.author), axis=1).to_list()


class TxtIngestor(IngestorInterface):
    """Imports quotes from raw text(txt) files."""

    allowed_extensions = ['txt']

    @classmethod
    def parse(cls, path: str) -> List[QuoteModel]:
        """Return a list of `QuoteModel` from parsing a txt file."""
        if not cls.can_ingest(path):
            raise ValueError(f"File Type not supported for {path}")
        lines = open(path, 'r').readlines()
        return [QuoteModel(body=cls.clean_text(ln.split("-")[0]),
                           author=cls.clean_text(ln.split("-")[1])) for ln in lines if cls.clean_text(ln)]


class Ingestor(IngestorInterface):
    """Encapsulates helper ingestor classes to a unified interface for all supported file types."""

    @classmethod
    def can_ingest(cls, path) -> bool:
        """Return a bool if the parent class has support for file extension in a given path."""
        return cls.ext_from_path(path) in cls.__base__.extension_support()

    @classmethod
    def parse(cls, path: str) -> List[QuoteModel]:
        """Return a list of `QuoteModel` from parsing any supported file type."""
        ext = cls.ext_from_path(path)
        base = cls.__base__

        if not cls.can_ingest(path):
            raise ValueError(f'Unsupported file extension "{ext}" from {path}. '
                             f'Supported types are -> {base.extension_support()}')

        parser = next((c for c in base.__subclasses__() if ext in c.allowed_extensions), None)
        return parser.parse(path)
