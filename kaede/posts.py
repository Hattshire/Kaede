#!/usr/bin/python3
from .image import Image


class Post():
	"""Contains details about a post. 

	:param data: Source data used to build the object on.
	:type data: dict

	.. warning:: `data` parameter must have `Post.__required_keys__` keys included.
	
	Use :py:func:`dir` to see available details.
	"""

	__required_keys__ = ('id', 'thumbnail_url', 'tags', 'image_url', 'rating')
	#                     str   str              set     str          str
	__standard_keys__ = ('author', 'date', 'hash', 'height', 'width')
	#                     str       int     str     int       int
	# 'sample_url's are optional, but recommended, as they're scaled down versions
	# of the original image and can be loaded quicker.

	def __init__(self, data):
		"""Init function.

		:param data: Source data used to build the object on. * Must have `Post.__required_keys__` keys included
		:type data: dict

		"""
		self._data = {}
		self.Image = None
		self.Sample = None
		self.Thumbnail = None

		for key in Post.__required_keys__:
			if key not in data:
				raise KeyError('Key `%s` not found on Post source data.' % key)
			self._data[key] = data[key]
		for key in Post.__standard_keys__:
			if key not in data:
				self._data[key] = 'Unknown'
			else:
				self._data[key] = data[key]

		if not isinstance(self._data['tags'], (tuple,list,set,frozenset)):
			raise TypeError('Invalid type of `tags` value (%s)' % str(type(self._data['tags'])))

		self.Thumbnail = Image(self._data['thumbnail_url'])
		self.Image = Image(self._data['image_url'])
		if 'sample_url' in data:
			self.Sample = Image(data['sample_url'])

	def __dir__(self):
		return {'image', 'sample', 'thumbnail', }.union(set(self._data.keys()))

	def __repr__(self):
		"""Create an string representation."""
		return self.__class__.__name__ + "(ID=\"" + str(self._data['id']) + "\")"

	def __getitem__(self, key):
		"""Emulate a mapping behaviour.
		
		Return the value stored in `key`.
		
		Args:
			key (str): Keyword to get the data from.
		"""
		if type(key) is str:
			if key in self._data:
				return self._data[key]
			if key == "thumbnail":
				return self.Thumbnail
			if key == "image":
				return self.Image
			if key == "sample":
				return self.Sample
		raise KeyError("The key `" + str(key) +
		               "`, of type `" + str(type(key)) +
		               "` is not valid. Use a valid string instead.")

	def __setitem__(self, key, value):
		"""Emulate a mapping behaviour.
		
		Set the value stored in `key` as `value`.
		
		Args:
			key (str): Keyword to put the data into.
			value (*): Value to store.
		"""
		if type(key) is str:
			self._data[key] = value
		else:
			raise KeyError("The key `" + str(key) +
			               "`, of type `" + str(type(key)) +
			               "` is not valid. Use an string instead.")

	def __contains__(self, key):
		"""Check for `key` existence.
		
		Args:
			key (str): Keyword to check.
		"""
		if key in self._data:
			return True
		else:
			return False

	def __iter__(self):
		"""Iterate over post items."""
		return self._data.items().__iter__()


class SearchHelper():
	"""Provides post management and cache.

	:param board_provider: An instance of Board.
	:type  board_provider: kaede.boards.Board
	:param tags: Keywords to search on the board.
	:type tags: list
	
	Usage:

		1. Create a new instance::

			bpv = Board()
			results = SearchHelper(bpv, tags=["red_eyes", "brown_hair"])

		2. Get elements::

			results.more()
			posts = [YourProcessPostsFn(post) for post in results]
		
		3. [...]
		4. Profit!
	"""

	def __init__(self, board_provider, tags=[]):
		"""Init function.
		
		Args:
			board_provider (Board): An instance of Board.
			tags (list): Keywords to search on the board.
		"""
		if type(tags) is not list:
			if type(tags) is str:
				self.tags = [tags.strip().split()]
			elif type(tags) is None:
				self.tags = []
			else:
				raise TypeError("No valid `tags` were given.")
		else:
			self.tags = tags
		self.loaded_pages = 0
		self.board_provider = board_provider
		self.posts = {}

	def __repr__(self):
		"""Create an string representation."""
		return "PostManager(count=%i, tags=[%s])" % (len(self.posts), ', '.join(self.tags))

	def __getitem__(self, post_id):
		"""Emulate a mapping behaviour.
		
		Returns the post from a given Post ID.
		
		Args:
			post_id (str): Post ID.
		"""
		if type(post_id) is int:
			return self.__getitem__(str(post_id))
		elif type(post_id) is str and post_id in self:
			return self.posts[post_id]
		else:
			raise KeyError(post_id)

	def __contains__(self, post_id):
		"""Check for `post_id` existence.
		
		Args:
			post_id (str): ID to check.
		"""
		if post_id in self.posts:
			return True
		else:
			return False

	def __iter__(self):
		"""Iterate over current items."""
		return self.posts.values().__iter__()

	def __call__(self):
		"""Search on instance call (shortcut for self.more)"""
		return self.more()
	
	def __len__(self):
		return len(self.posts)

	def ids(self):
		"""Retrieve the stored post ids."""
		return self.posts.keys().__iter__()

	def more(self):
		"""Retrieve the next load of posts."""
		tags = self.tags.copy()
		data = self.board_provider.search(tags, self.loaded_pages)

		if(data):
			self.loaded_pages += 1
			for item in data:
				if str(item['id']) not in self.posts:
					self.posts[str(item['id'])] = item
				yield item
