import httpretty
import json
from kaede import boards, posts, image

post_magic_data = {
	"id": 0,
	"thumbnail_url": "http://example.com/thumb_example.png",
	"image_url": "http://example.com/example.png",
	"author": "da_lazer",
	"tags": ["end", "da", "lazer"],
	"rating": "safe"
}


class MockProvider(boards.Board):
	__DEFAULT_DATA__ = {"type": "foo", "filename": "bar.baz"}

	@staticmethod
	def _list_url(tags=None, page=0):
		return "http://examp.le/list/" + str(page) + "/" + str(tags)

	@staticmethod
	def _image_url(post_data):
		return "http://examp.le/{}/{}" % (post_data['type'], post_data['filename'])
	
	@staticmethod
	def _thumbnail_url(post_data):
		return MockProvider._image_url(post_data)

	@staticmethod
	def _sample_url(post_data):
		return MockProvider._image_url(post_data)


@httpretty.activate
def test_boards_Board_search():
	httpretty.enable()

	image_url = "http://examp.le/foo/bar.baz"
	image_body = b"imagecontent"
	httpretty.register_uri(httpretty.GET, image_url, body=image_body)

	page_num = 365
	tags = ["abcdche" "rating:s"]
	search_url = "http://examp.le/list/" + str(page_num) + "/" + '+'.join(tags)
	search_body = []
	pmd = post_magic_data
	for num in range(0, 100):
		pmd['id'] = num
		pmd['image_url'] = image_url
		pmd['thumbnail_url'] = image_url
		pmd['sample_url'] = image_url
		search_body.append(pmd)
	search_body = json.dumps(search_body)
	httpretty.register_uri(httpretty.GET, search_url, body=search_body)

	foo = MockProvider.search(tags, page_num)
	bar = next(foo)
	assert(type(bar) is posts.Post)
	bar['image'].load()
	bar['thumbnail'].load()
	bar['sample'].load()
	baz = image.Image(image_url)
	baz.load()
	assert(bar['image'].buffer == baz.buffer)
	assert(bar['thumbnail'].buffer == baz.buffer)
	assert(bar['sample'].buffer == baz.buffer)

	httpretty.disable()
	httpretty.reset()
