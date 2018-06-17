import httpretty
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
