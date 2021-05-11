import httpretty
import json
import re
from kaede import boards, posts, image

post_magic_data = {
	"id": 0,
	"thumbnail_url": "http://example.com/thumb_example.png",
	"image_url": "http://example.com/example.png",
	"author": "da_lazer",
	"tags": ("end", "da", "lazer"),
	"rating": "safe"
}


class MockProvider(boards.Board):
	__DEFAULT_DATA__ = {"type": "foo", "filename": "bar.baz"}
	_image_body = b"imagecontent"
	_page_num = 365
	_tags = ["abcdche", "rating:s"]

	@staticmethod
	def mockprepare():
		httpretty.register_uri(httpretty.GET, MockProvider._image_url(MockProvider.__DEFAULT_DATA__), body=MockProvider._image_body)

		search_url = "http://examp.le/list/" + str(MockProvider._page_num) + "/" + '+'.join(MockProvider._tags)
		search_url = re.compile(r"http://examp.le/list/\d+/.*")
		search_body = []
		for num in range(0, 100):
			pmd=post_magic_data.copy()
			pmd['id'] = num
			pmd['image_url'] = MockProvider._image_url(MockProvider.__DEFAULT_DATA__)
			pmd['thumbnail_url'] = MockProvider._image_url(MockProvider.__DEFAULT_DATA__)
			pmd['sample_url'] = MockProvider._image_url(MockProvider.__DEFAULT_DATA__)
			search_body.append(pmd)
		search_body = json.dumps(search_body)
		httpretty.register_uri(httpretty.GET, search_url, body=search_body)

	@staticmethod
	def _list_url(tags=None, page=0):
		return "http://examp.le/list/" + str(page) + "/" + str(tags)

	@staticmethod
	def _image_url(post_data):
		return "http://examp.le/" + post_data['type'] + "/" + post_data['filename']
	
	@staticmethod
	def _thumbnail_url(post_data):
		return MockProvider._image_url(post_data)

	@staticmethod
	def _sample_url(post_data):
		return MockProvider._image_url(post_data)


@httpretty.activate
def test_boards_Board_search():
	httpretty.enable()

	MockProvider.mockprepare()

	foo = MockProvider.search(MockProvider._tags, MockProvider._page_num)
	bar = next(foo)
	assert(type(bar) is posts.Post)
	bar['image'].load()
	bar['thumbnail'].load()
	bar['sample'].load()
	baz = image.Image(MockProvider._image_url(MockProvider.__DEFAULT_DATA__))
	baz.load()
	assert(bar['image'].buffer == baz.buffer)
	assert(bar['thumbnail'].buffer == baz.buffer)
	assert(bar['sample'].buffer == baz.buffer)

	httpretty.disable()
	httpretty.reset()
