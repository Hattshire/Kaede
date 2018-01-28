import requests


class BoardProvider():
    """Base for a imageboard provider."""

    def _url(self, key, tags=None, page=0):
        """Construct the base url."""
        pass

    def _image_url(self, post_data):
        """Construct the image url."""
        pass

    def _thumbnail_url(self, post_data):
        """Construct the thumbnail url."""
        pass

    def get_posts(self):
        """Retrieve the latest images."""
        return requests.get(self._url('list')).json()

    def get_image(self, post_data):
        """Retrieve an image.

        Args:
            post_data (dict): Image information.
        """
        return requests.get(self._image_url(post_data)).content

    def get_thumbnail(self, post_data):
        """Retrieve a thumbnail.

        Args:
            post_data (dict): Image information.
        """
        return requests.get(self._thumbnail_url(post_data)).content

    def search(self, tags, page=0):
        """Get a list of image informations.

        Args:
            tags (list): A list of tags.
            page (int): Page to retrieve.
        """
        tag_string = '+'.join(tags)
        response = requests.get(self.url('list', tag_string, page))
        result = []

        if(response.content):
            result = response.json()
        for item in result:
            yield item


class GelbooruProvider(BoardProvider):
    """Board provider for Gelbooru."""

    def _url(self, key, tags=None, page=0):
        tail = {'list': "&s=post",
                'comments': "&s=comment"}
        return "http://gelbooru.com/index.php?page=dapi&json=1&q=index" + \
                tail[key] + "&tags=" + str(tags) + "&pid=" + str(page)

    def _image_url(self, post_data):
        url = post_data['file_url']
        return url

    def _thumbnail_url(self, post_data):
        url = "http://simg3.gelbooru.com/thumbnails/" + \
              post_data['directory'] + '/thumbnail_' + \
              post_data['hash'] + '.jpg'
        return url


class TbibProvider(BoardProvider):
    """Board provider for The big image board."""

    def _url(self, key, tags=None, page=0):
        tail = {'list': "&s=post",
                'comments': "&s=comment"}
        return "http://tbib.org/index.php?page=dapi&json=1&q=index" + \
               tail[key] + "&tags=" + str(tags) + "&pid=" + str(page)

    def _image_url(self, post_data):
        url = "http://tbib.org//images/" + \
              post_data['directory'] + '/' + post_data['image']
        return url

    def _thumbnail_url(self, post_data):
        url = "http://tbib.org/thumbnails/" + \
              post_data['directory'] + '/thumbnail_' + post_data['image']
        return url


class Image():
    """Image object."""

    def load():
        pass

    def unload():
        pass


class Thumbnail(Image):
    """Thumbnail image."""

    pass


class Post():
    """Post object.

    Contains details about a post, and provides methods to manipulate them.
    """

    __required_keys__ = ('id', 'thumbnail_url', 'image_url')
    __standard_keys__ = ('author', 'date', 'rating', 'hash', 'height', 'width')

    def __init__(self, raw_data):
        """Init function."""
        self.last_access = 0
        self.last_listing = 0
        self.raw_data = raw_data
        for key in Post.__required_keys__:
            if key not in self.raw_data:
                raise KeyError('Key `%s` not found on Post source data.' % key)
        for key in Post.__standard_keys__:
            if key not in self.raw_data:
                self.raw_data[key] = 'Unknown'

    def __repr__(self):
        """Create an string representation."""
        return "Post(ID=" + str(self.raw_data['id']) + ")"

    def __getitem__(self, key):
        """Emulate a mapping behaviour."""
        if type(key) is str:
            return self.raw_data[key]
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        """Emulate a mapping behaviour."""
        self.raw_data[key] = value

    def __contains__(self, key):
        """Search for `key` existence."""
        if key in self.raw_data:
            return True
        else:
            return False

    def __iter__(self):
        """Iterate over post items."""
        return self.raw_data.items().__iter__()


class PostManager():
    """Provides post management capabilities."""

    def __init__(self, tags=[], board_provider=TbibProvider,
                 async=True, preload=True):
        """Init function."""
        self.async = True
        self.tags = tags
        self.loaded_pages = 0
        self.board_provider = board_provider()
        self.posts = {}

    def __repr__(self):
        """Create an string representation."""
        return "PostManager(count=%i, tags=[%s])" % (len(self.posts),
                                                     ', '.join(self.tags))

    def __getitem__(self, key):
        """Emulate a mapping behaviour."""
        if type(key) is int:
            pass
        elif type(key) is str:
            if key not in self.posts:
                self.do_search(['id:'+key])
            return self.posts[key]
        else:
            raise KeyError(key)

    def __contains__(self, key):
        """Search for `key` existence."""
        if key in self.posts:
            return True
        else:
            return False

    def __iter__(self):
        """Iterate over current items."""
        return self.posts.values().__iter__()

    def __call__(self, tags=None):
        """Search on instance call."""
        return self.do_search(tags)

    def do_search(self, tags=None):
        """Retrieve a bunch of posts according to the tags."""
        if tags is None:
            tags = self.tags
        elif type(tags) is str:
            tags = [tags]
        data = self.board_provider.search(tags, 0)

        if(data):
            for item in data:
                if str(item['id']) not in self.posts:
                    self.posts[str(item['id'])] = item
