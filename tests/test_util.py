import httpretty
import time
import os.path
from tempfile import NamedTemporaryFile
from libkaede import util


def test_Image_init():
	url = "https://example.com/example.png"
	image = util.Image(url)
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

	image = util.Image(image_url)
	image.load(async=False)

	assert(image.progress == float(1))
	assert(image.size == len(image_body))
	assert(image.buffer == image_body)
	assert(len(image.buffer) == image.size)


	image = util.Image(image_url)
	image.load()

	assert(image.progress == float(1))
	assert(image.size == len(image_body))
	assert(image.buffer == image_body)
	assert(len(image.buffer) == image.size)

def test_Image_load_async():
	image_url = "http://example.com/example.png"
	image_body = b"imagecontent"
	httpretty.enable()
	httpretty.register_uri(httpretty.GET, image_url, body=image_body)

	image = util.Image(image_url)
	image.load(async=True)
	
	time.sleep(0.1)

	assert(image.progress == float(1))
	assert(image.size == len(image_body))
	assert(image.buffer == image_body)
	assert(len(image.buffer) == image.size)

def test_Image_unload():
	image_url = "http://example.com/example.png"
	image_body = b"imagecontent"
	httpretty.enable()
	httpretty.register_uri(httpretty.GET, image_url, body=image_body)

	image = util.Image(image_url)
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

def test_Image_save():
	file = NamedTemporaryFile(delete=False)
	file.close()
	filename = os.path.basename(file.name)
	folder = os.path.dirname(file.name)
	image_url = "http://example.com/example.png"
	image_body = b"imagecontent"
	httpretty.enable()
	httpretty.register_uri(httpretty.GET, image_url, body=image_body)

	image = util.Image(image_url)
	image.load()

	image.save(folder, filename)

	with open(file.name, 'rb') as test_file:
		test_file_contents = test_file.read()
		assert(test_file_contents == image_body)

	image = util.Image(image_url)
	image.load(async=False)

	image.save(folder, filename)

	with open(file.name, 'rb') as test_file:
		test_file_contents = test_file.read()
		assert(test_file_contents == image_body)

def test_Image_save_async():
	file = NamedTemporaryFile(delete=False)
	file.close()
	filename = os.path.basename(file.name)
	folder = os.path.dirname(file.name)
	image_url = "http://example.com/example.png"
	image_body = b"imagecontent"
	httpretty.enable()
	httpretty.register_uri(httpretty.GET, image_url, body=image_body)

	image = util.Image(image_url)
	image.load(async=True)

	time.sleep(0.1)

	image.save(folder, filename)

	with open(file.name, 'rb') as test_file:
		test_file_contents = test_file.read()
		assert(test_file_contents == image_body)
