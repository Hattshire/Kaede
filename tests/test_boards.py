import httpretty
import pytest
import json
import re
from kaede import boards, posts, image

post_magic_data = {
	"id": 0,
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
	def mockprepare(explicit_urls=True):
		httpretty.register_uri(httpretty.GET, MockProvider._image_url(MockProvider.__DEFAULT_DATA__), body=MockProvider._image_body)

		search_url = re.compile(r"http://examp.le/list/\d+/.*")
		search_body = []
		for num in range(0, 100):
			pmd=post_magic_data.copy()
			pmd['id'] = num
			if explicit_urls:
				pmd['image_url'] = MockProvider._image_url(MockProvider.__DEFAULT_DATA__)
				pmd['thumbnail_url'] = MockProvider._image_url(MockProvider.__DEFAULT_DATA__)
				pmd['sample_url'] = MockProvider._image_url(MockProvider.__DEFAULT_DATA__)
			else:
				pmd['sample'] = "a"
			search_body.append(pmd)
		search_body = json.dumps(search_body)
		httpretty.register_uri(httpretty.GET, search_url, body=search_body)

	@staticmethod
	def _list_url(tags=None, page=0):
		return "http://examp.le/list/" + str(page) + "/" + str(tags)

	@staticmethod
	def _image_url(post_data):
		return "http://examp.le/foo/bar.baz"
	
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


	MockProvider.mockprepare(False)
	foo = MockProvider.search(MockProvider._tags, MockProvider._page_num)
	bar = next(foo)
	assert(type(bar) is posts.Post)

	httpretty.disable()
	httpretty.reset()

@httpretty.activate
def test_boards_Board_get_posts():
	httpretty.enable()
	MockProvider.mockprepare()

	foo = list(MockProvider.search([], 0))
	bar = list(MockProvider.get_posts())

	assert(len(foo) == len(bar))
	for n in range(len(foo)):
		assert(foo[n]['id'] == bar[n]['id'])

	httpretty.disable()
	httpretty.reset()

def test_boards_Board_NotImplemented():
	with pytest.raises(NotImplementedError):
		a=boards.Board._list_url()
	with pytest.raises(NotImplementedError):
		a=boards.Board._image_url({})
	with pytest.raises(NotImplementedError):
		a=boards.Board._thumbnail_url({})
	with pytest.raises(NotImplementedError):
		a=boards.Board._sample_url({})

def test_boards_GelbooruProvider_list_url():
	foo = boards.GelbooruProvider._list_url()
	fooc = "http://gelbooru.com/index.php?page=dapi&json=1&q=index&s=post&tags=&pid=0"

	bar = boards.GelbooruProvider._list_url(None, 0)

	baz = boards.GelbooruProvider._list_url("foo bar", 321)
	bazc = "http://gelbooru.com/index.php?page=dapi&json=1&q=index&s=post&tags=foo bar&pid=321"

	assert(foo == fooc)
	assert(bar == fooc)
	assert(baz == bazc)

	with pytest.raises(TypeError):
		a = boards.GelbooruProvider._list_url([])

def test_boards_GelbooruProvider_image_url():
	data = {'file_url': 'http://ur.l/',}
	assert(boards.GelbooruProvider._image_url(data) == data['file_url'])
	with pytest.raises(KeyError):
		a = boards.GelbooruProvider._image_url({})

def test_boards_GelbooruProvider_thumbnail_url():
	data = {'directory': 'ab1', 'hash': 'a1b2c3d4'}
	file_url = "http://img2.gelbooru.com/thumbnails/ab1/thumbnail_a1b2c3d4.jpg"
	assert(boards.GelbooruProvider._thumbnail_url(data) == file_url)
	with pytest.raises(KeyError):
		a = boards.GelbooruProvider._image_url({})

def test_boards_GelbooruProvider_sample_url():
	data = {'file_url': 'http://ur.l/',}
	assert(boards.GelbooruProvider._sample_url(data) == data['file_url'])
	with pytest.raises(KeyError):
		a = boards.GelbooruProvider._sample_url({})


def test_boards_TbibProvider_list_url():
	foo = boards.TbibProvider._list_url()
	fooc = "http://tbib.org/index.php?page=dapi&json=1&q=index&s=post&tags=&pid=0"

	bar = boards.TbibProvider._list_url(None, 0)

	baz = boards.TbibProvider._list_url("foo bar", 321)
	bazc = "http://tbib.org/index.php?page=dapi&json=1&q=index&s=post&tags=foo bar&pid=321"

	assert(foo == fooc)
	assert(bar == fooc)
	assert(baz == bazc)

	with pytest.raises(TypeError):
		a = boards.TbibProvider._list_url([])

def test_boards_TbibProvider_image_url():
	data = {'directory': 'ab1', 'image': 'a1.png'}
	file_url = "http://tbib.org//images/ab1/a1.png"
	assert(boards.TbibProvider._image_url(data) == file_url)
	with pytest.raises(KeyError):
		a = boards.TbibProvider._image_url({})

def test_boards_TbibProvider_thumbnail_url():
	data = {'directory': 'ab1', 'image': 'a1.png'}
	file_url = "http://tbib.org/thumbnails/ab1/thumbnail_a1.jpg"
	assert(boards.TbibProvider._thumbnail_url(data) == file_url)
	with pytest.raises(KeyError):
		a = boards.TbibProvider._thumbnail_url({})

def test_boards_TbibProvider_sample_url():
	data = {'directory': 'ab1', 'image': 'a1.png'}
	file_url = "http://tbib.org//images/ab1/a1.png"
	assert(boards.TbibProvider._sample_url(data) == file_url)
	with pytest.raises(KeyError):
		a = boards.TbibProvider._sample_url({})