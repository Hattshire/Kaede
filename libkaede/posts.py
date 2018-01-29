import requests
from multiprocessing.pool import ThreadPool
from .boards import TbibProvider

WORKER_POOL = ThreadPool()


class Image():
    """Image object."""

    def __init__(self, url):
        """Init function.

        Args:
            url (str): Where the image is located.
        """
        self.url = url
        self.buffer = bytearray()
        self.size = 0
        self.progress = 0

    def load(self):
        """Load the image."""
        global WORKER_POOL
        WORKER_POOL.apply_async(self._async_loader)

    def _async_loader(self):
        data_stream = requests.get(self.url, stream=True).raw
        self.size = data_stream.getheader('Content-Length')
        for data in data_stream.stream(amt=None, decode_content=True):
            if data:
                self.buffer.extend(data)
            if self.size is not None:
                self.progress = int(self.size) / data_stream.tell()

    def unload(self):
        """Remove the image from memory."""
        self.bytes = b''

    def save(self, folder, filename=None):
        """Save the image to disk.

        Args:
            folder (str): Where to save.
            filename (str): How to name.
        """
        global WORKER_POOL
        WORKER_POOL.apply_async(self._async_save, (folder, filename))

    def _async_save(self, folder, filename):
        if filename is None:
            filename = self.url.split('/')[-1]
        with open(folder+filename, 'wb') as output_file:
            output_file.write(self.buffer)


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
        """Init function.

        Args:
            raw_data (dict): Source data used to build the object on.
        """
        self.last_access = 0
        self.last_listing = 0
        self.raw_data = raw_data
        self.Image = None
        self.Sample = None
        self.Thumbnail = None

        for key in Post.__required_keys__:
            if key not in self.raw_data:
                raise KeyError('Key `%s` not found on Post source data.' % key)
        for key in Post.__standard_keys__:
            if key not in self.raw_data:
                self.raw_data[key] = 'Unknown'

        self.Thumbnail = Image(self.raw_data['thumbnail_url'])
        self.Thumbnail.load()
        self.Image = Image(self.raw_data['image_url'])
        if 'sample' in self.raw_data:
            self.Sample = Image(self.raw_data['sample_url'])

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
        try:
            data = self.board_provider.search(tags, 0)
        except requests.exceptions.ConnectionError:
            data = None

        if(data):
            for item in data:
                if str(item['id']) not in self.posts:
                    self.posts[str(item['id'])] = Post(item)
