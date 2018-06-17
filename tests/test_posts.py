from libkaede import posts, util

post_magic_data = {
	"id": "2450003",
	"thumbnail_url": "http://example.com/thumb_example.png",
	"image_url": "http://example.com/example.png",
	"author": "da_lazer"
}

image_data = b"imagedata"

def test_Post():
	post = posts.Post(post_magic_data)
	assert(type(post.Image) == util.Image)
	assert(type(post.Thumbnail) == util.Image)
	
	#getitem
	assert(post["author"] == "da_lazer")
	assert(post["image"] == post.Image)
	assert(post["thumbnail"] == post.Thumbnail)
	
	#setitem
	post["author"] = "no_lazer"
	assert(post["author"] == "no_lazer")
	
	#contains
	assert("image_url" in post)
	assert("lazert" not in post)

	#iter
	a = []
	for item in post:
		a.append(item)
	assert(len(a) == len(list(post_magic_data)))

