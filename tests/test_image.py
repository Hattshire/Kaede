from tempfile import NamedTemporaryFile
from kaede.image import Image
import httpretty
import pytest
import os.path


def test_Image_init():
	url = "https://example.com/example.png"
	image = Image(url)
	assert(image.url == url)
	assert(type(image.buffer) == bytearray)
	assert(image.buffer == b'')
	assert(image.size == 0)
	assert(image.progress == float(0))


@httpretty.activate
def test_Image_load():
	image_url = "http://example.com/example.png"
	image_body = b"imagecontent"
	httpretty.enable()
	httpretty.register_uri(httpretty.GET, image_url, body=image_body)

	image = Image(image_url)
	image.load()

	assert(image.progress == float(1))
	assert(image.size == len(image_body))
	assert(image.buffer == image_body)
	assert(len(image.buffer) == image.size)
	with pytest.raises(RuntimeError):
		image.load()
	
	image_url = "http://example.com/example2.png"
	image_body = b""
	httpretty.register_uri(httpretty.GET, image_url, body=image_body)
	image = Image(image_url)
	with pytest.raises(ValueError):
		image.load()
	
	httpretty.disable()
	httpretty.reset()


@httpretty.activate
def test_Image_unload():
	image_url = "http://example.com/example.png"
	image_body = b"imagecontent"
	httpretty.enable()
	httpretty.register_uri(httpretty.GET, image_url, body=image_body)

	image = Image(image_url)

	assert(type(image.buffer) == bytearray)
	assert(image.buffer == b'')
	assert(image.size == 0)
	assert(image.progress == float(0))

	image.load()

	assert(image.progress == float(1))
	assert(image.size == len(image_body))
	assert(image.buffer == image_body)
	assert(len(image.buffer) == image.size)

	image.unload()

	assert(type(image.buffer) == bytearray)
	assert(image.buffer == b'')
	assert(image.size == 0)
	assert(image.progress == float(0))
	httpretty.disable()
	httpretty.reset()


@httpretty.activate
def test_Image_save():
	file = NamedTemporaryFile(delete=False)
	file.close()
	filename = os.path.basename(file.name)
	folder = os.path.dirname(file.name)
	image_url = "http://example.com/example.png"
	image_body = b"imagecontent"
	httpretty.enable()
	httpretty.register_uri(httpretty.GET, image_url, body=image_body)

	image = Image(image_url)
	image.load()

	image.save(folder, filename)
	image.save(folder)

	with open(file.name, 'rb') as test_file:
		test_file_contents = test_file.read()
		assert(test_file_contents == image_body)
	httpretty.disable()
	httpretty.reset()
