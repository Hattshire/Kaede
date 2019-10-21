from kaede import posts, image

post_magic_data = {
	"id": "2450003",
	"thumbnail_url": "http://example.com/thumb_example.png",
	"image_url": "http://example.com/example.png",
	"author": "da_lazer",
	"tags": ["end", "da", "lazer"],
	"rating": "safe"
}

image_data = b"imagedata"


def test_posts_Post():
	post = posts.Post(post_magic_data)
	assert(type(post['image']) is image.Image)
	assert(type(post['thumbnail']) is image.Image)
	
	# getitem
	assert(post["author"] == "da_lazer")
	assert(post["tags"] == post_magic_data["tags"])
	
	# setitem
	post["author"] = "no_lazer"
	assert(post["author"] == "no_lazer")
	
	# contains
	assert("image_url" in post)
	assert("lazert" not in post)

	# iter
	a = []
	for item in post:
		a.append(item)
	assert(len(a) == len(
		posts.Post.__required_keys__ + posts.Post.__standard_keys__
	))


def test_posts_SearchHelper():
	pass