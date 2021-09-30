"""Flask web application interface to meme generation."""
import random
import os
import tempfile
from itertools import chain

import requests
from PIL import Image
from flask import Flask, render_template, abort, request

import quoteengine
from memeengine.meme_generator import MemeGenerator
from quoteengine.ingestors import Ingestor

app = Flask(__name__)

meme = MemeGenerator('./static')


def setup():
    """Load all resources."""
    quote_files = ['./_data/DogQuotes/DogQuotesTXT.txt',
                   './_data/DogQuotes/DogQuotesDOCX.docx',
                   './_data/DogQuotes/DogQuotesPDF.pdf',
                   './_data/DogQuotes/DogQuotesCSV.csv']
    quotes = list(chain(*[Ingestor.parse(f) for f in quote_files]))

    images_path = "./_data/photos/dog/"
    imgs = [f"{images_path}/{f}" for f in os.listdir(images_path) if f.endswith(".jpg")]

    return quotes, imgs


quotes, imgs = setup()


@app.route('/')
def meme_rand():
    """Generate a random meme."""
    img = random.choice(imgs)
    quote = random.choice(quotes)
    path = meme.make_meme(img, quote.body, quote.author)
    return render_template('meme.html', path=path)


@app.route('/create', methods=['GET'])
def meme_form():
    """User input for meme information."""
    return render_template('meme_form.html')


@app.route('/create', methods=['POST'])
def meme_post():
    """Create a user defined meme."""
    r = requests.get(request.form['image_url'], allow_redirects=True, stream=True)

    tmp_file = tempfile.NamedTemporaryFile(prefix='meme-gen-web-dl-', suffix='.jpg', delete=False).name
    try:
        Image.open(r.raw).save(tmp_file)
    except OSError:
        print(f"cannot convert file to jpg")

    quote = quoteengine.QuoteModel(body=request.form['body'], author=request.form['author'])
    path = meme.make_meme(tmp_file, quote.body, quote.author)

    os.unlink(tmp_file)

    return render_template('meme.html', path=path)


if __name__ == "__main__":
    app.run()
