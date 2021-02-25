#!/usr/bin/python3
import requests
import os
from .posts import Post


class Board():
	"""Base for a imageboard provider.

	Example usage::

		from kaede.boards import Board

		for post in Board.search(["tags"], page=0):
			...


	Implementation of new `Board`:
	
		- For simple danbooru-compatible boards, override :py:meth:`._list_url`,
		  :py:meth:`_image_url`, :py:meth:`_thumbnail_url` and :py:meth:`._sample_url` with the
		  corresponding uris.
		
		- For other kind of boards, like chans, override :py:meth:`.search` with a generator that yields :py:class:`kaede.posts.Post` .

	"""

	@staticmethod
	def _list_url(tags=None, page=0):
		"""Construct the post listing url.
		
		:param tags: Keywords to search for.
		:type tags: list or str or None
		:param page: Search page to show.
		:type page: int
		:rtype: str
		"""
		pass

	@staticmethod
	def _image_url(post_data):
		"""Construct the image url.
		
		:param post_data: Raw board post data.
		:type post_data: dict
		:rtype: str
		"""
		pass

	@staticmethod
	def _thumbnail_url(post_data):
		"""Construct the thumbnail url.
		
		:param post_data: Raw board post data.
		:type post_data: dict
		:rtype: str
		"""
		pass

	@staticmethod
	def _sample_url(post_data):
		"""Construct the sample url.
		
		:param post_data: Raw board post data.
		:type post_data: dict
		:rtype: str
		"""
		pass

	@classmethod
	def get_posts(cls):
		"""Retrieve the latest posts.

		Shortcut for `Board.search([],0)`.
		"""
		return cls.search([])

	@classmethod
	def search(cls, tags, page=0):
		"""Get a list of posts' metadata.

		:param tags: A list of tags.
		:type tags: list
		:param page: Page to retrieve.
		:type page: int
		:rtype: Iterator that yields :py:class:`kaede.posts.Post`
		"""
		tag_string = '+'.join(tags)
		response = requests.get(cls._list_url(tag_string, page))
		result = []

		if(response.content):
			result = response.json()
		for item in result:
			if 'thumbnail_url' not in item:
				item['thumbnail_url'] = cls._thumbnail_url(item)
			if 'image_url' not in item:
				item['image_url'] = cls._image_url(item)
			if 'sample_url' not in item and 'sample' in item:
				item['sample_url'] = cls._sample_url(item)
			yield Post(item)


class GelbooruProvider(Board):
	"""Board provider for Gelbooru."""

	@staticmethod
	def _list_url(tags=None, page=0):
		return "http://gelbooru.com/index.php?page=dapi&json=1&q=index" + \
		       "&s=post" + "&tags=" + str(tags) + "&pid=" + str(page)

	@staticmethod
	def _image_url(post_data):
		return post_data['file_url']

	@staticmethod
	def _thumbnail_url(post_data):
		return "http://img2.gelbooru.com/thumbnails/" + \
		       post_data['directory'] + '/thumbnail_' + \
		       post_data['hash'] + '.jpg'

	@staticmethod
	def _sample_url(post_data):
		# TODO Implement sample urls for gelbooru
		return GelbooruProvider._image_url(post_data)


class TbibProvider(Board):
	"""Board provider for The big image board."""

	@staticmethod
	def _list_url(tags=None, page=0):
		return "http://tbib.org/index.php?page=dapi&json=1&q=index" + \
		       "&s=post" + "&tags=" + str(tags) + "&pid=" + str(page)

	@staticmethod
	def _image_url(post_data):
		return "http://tbib.org//images/" + \
		       post_data['directory'] + '/' + post_data['image']

	@staticmethod
	def _thumbnail_url(post_data):
		return "http://tbib.org/thumbnails/" + \
		       post_data['directory'] + '/thumbnail_' + os.path.splitext(post_data['image'])[0] + ".jpg"

	@staticmethod
	def _sample_url(post_data):
		# TODO Implement sample urls for tbib
		return TbibProvider._image_url(post_data)
