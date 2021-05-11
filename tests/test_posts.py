import httpretty, json
import pytest
from .test_boards import MockProvider
from kaede import posts, image

post_magic_data = {
	"id": "2450003",
	"thumbnail_url": "http://example.com/thumb_example.png",
	"image_url": "http://example.com/example.png",
	"author": "da_lazer",
	"tags": ("end", "da", "lazer"),
	"rating": "safe"
}

image_data = b"imagedata"


def test_posts_Post_emptyMeta():
	with pytest.raises(KeyError):
		a=posts.Post({})

def test_posts_Post_goodMetaLoad():
	post = posts.Post(post_magic_data)

	assert(type(post['image']) is image.Image)
	assert(type(post['thumbnail']) is image.Image)
	
def test_posts_Post_getItem():
	post = posts.Post(post_magic_data)

	assert(post["author"] == "da_lazer")
	assert(post["tags"] == post_magic_data["tags"])
		
def test_posts_Post_setItem():
	post = posts.Post(post_magic_data)

	post["author"] = "no_lazer"
	assert(post["author"] == "no_lazer")
		
def test_posts_Post_contains():
	post = posts.Post(post_magic_data)

	assert("image_url" in post)
	assert("lazert" not in post)
	
def test_posts_Post_iter():
	post = posts.Post(post_magic_data)

	a = []
	for item in post:
		a.append(item)
	assert(len(a) == len(
		posts.Post.__required_keys__ + posts.Post.__standard_keys__
	))
	
def test_posts_Post_dir():
	post = posts.Post(post_magic_data)

	a = dir(post)
	assert(set(post_magic_data.keys()).union({'image', 'sample', 'thumbnail'}).union(posts.Post.__standard_keys__) == set(a))

def test_posts_Post_badKeyGet():
	post = posts.Post(post_magic_data)

	with pytest.raises(KeyError):
		a=post['unexistant_key']

def test_posts_Post_badKeySet():
	post = posts.Post(post_magic_data)

	with pytest.raises(KeyError):
		post[0]=True


@httpretty.activate
def test_posts_SearchHelper():
	httpretty.enable()
	sh = posts.SearchHelper(MockProvider())
	assert(len(sh.posts) is 0)
	assert(len(sh) is 0)
	assert(len(sh.tags) is 0)
	assert(sh.loaded_pages is 0)
	assert(sh.board_provider is not None)

@httpretty.activate
def test_posts_SearchHelper_getItem():
	MockProvider.mockprepare()

	sh = posts.SearchHelper(MockProvider)
	foo = MockProvider.search(MockProvider._tags, MockProvider._page_num)
	bar = next(foo)
	with pytest.raises(KeyError):
		sh[0]
	a=sh.more()
	a=next(a)
	print(sh.posts)
	assert(sh[0])

	httpretty.disable()
	httpretty.reset()
