import requests
from .util import Image


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
		#TODO: Abstract the process
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
		self.Image = Image(self.raw_data['image_url'])
		if 'sample_url' in self.raw_data:
			self.Sample = Image(self.raw_data['sample_url'])

	def __repr__(self):
		"""Create an string representation."""
		return self.__class__.__name__ + "(ID=" + str(self.raw_data['id']) + "\""

	def __getitem__(self, key):
		"""Emulate a mapping behaviour.
		
		Return the value stored in `key`.
		
		Args:
			key (str): Keyword to get the data from.
		"""
		if type(key) is str:
			if key in self.raw_data:
				return self.raw_data[key]
			if key == "thumbnail":
				return self.Thumbnail
			if key == "image":
				return self.Image
			if key == "sample":
				return self.Sample
		else:
			raise KeyError("The key `" + str(key) + \
						   "`, of type `" + str(type(key)) + \
						   "` is not valid. Use a valid string instead.")

	def __setitem__(self, key, value):
		"""Emulate a mapping behaviour.
		
		Set the value stored in `key` as `value`.
		
		Args:
			key (str): Keyword to put the data into.
			value (*): Value to store.
		"""
		if type(key) is str:
			self.raw_data[key] = value
		else:
			raise KeyError("The key `" + str(key) + \
						   "`, of type `" + str(type(key)) + \
						   "` is not valid. Use an string instead.")

	def __contains__(self, key):
		"""Check for `key` existence.
		
		Args:
			key (str): Keyword to check.
		"""
		if key in self.raw_data:
			return True
		else:
			return False

	def __iter__(self):
		"""Iterate over post items."""
		return self.raw_data.items().__iter__()


class PostManager():
	"""Provides post management capabilities."""

	def __init__(self, board_provider, tags=[],
				 async=True, preload=True):
		"""Init function.
		
		Args:
			board_provider (BoardProvider): An instance of BoardProvider.
			tags (list): Keywords to search on the board.
			async (bool): Get the data asynchronously.
			preload (bool): Get the data on init.
		"""
		#TODO: Implement preload
		self.async = async
		self.tags = tags
		self.loaded_pages = 0
		self.board_provider = board_provider
		self.posts = {}

	def __repr__(self):
		"""Create an string representation."""
		return "PostManager(count=%i, tags=[%s])" % (len(self.posts),
													 ', '.join(self.tags))

	def __getitem__(self, key):
		"""Emulate a mapping behaviour.
		
		Return the value stored in `key`.
		
		Args:
			key (str): Keyword to get the data from.
		"""
		if type(key) is int:
			#TODO: handle int keys.
			pass
		elif type(key) is str:
			if key not in self.posts:
				self.search(['id:'+key])
			return self.posts[key]
		else:
			raise KeyError(key)

	def __contains__(self, key):
		"""Check for `key` existence.
		
		Args:
			key (str): Keyword to check.
		"""
		if key in self.posts:
			return True
		else:
			return False

	def __iter__(self):
		"""Iterate over current items."""
		return self.posts.values().__iter__()

	def __call__(self, tags=None):
		"""Search on instance call.
		
		Args:
			tags (list|str|None): Keywords to search for.
		"""
		return self.search(tags)

	def search(self, tags=None):
		"""Retrieve a bunch of posts according to the tags.
		
		Args:
			tags (list|str): Keywords to search for.
		"""
		#TODO: reset page count on tags change
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
