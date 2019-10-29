#!/usr/bin/python3
import requests
import os
from .posts import Post


class Board():
	""" Base for a imageboard provider.

		<This class does not save states, and thus can be used uninitialized>
		Usage:
			- Board.search(["tags"], page=0):
				Returns the last posts available for the tags specified, with
				an offset of `page` pages.
			- Board.get_posts():
				Shortcut for Board.search([],0). Gets the only the latest posts.

		Implementation of new `Board`:
			- For simple, danbooru compatible boards, override `_list_url`,
			  `_image_url`, `_thumbnail_url` and `_sample_url` with the
			  corresponding uris
			- For other kind of boards, like chans, override `search` with a
			  generator that yields `Post`s
	"""

	@staticmethod
	def _list_url(tags=None, page=0):
		"""Construct the post listing url.
		
		Args:
			tags (list|str|None): Keywords to search for.
			page (int): Search page to show.
		"""
		pass

	@staticmethod
	def _image_url(post_data):
		"""Construct the image url.
		
		Args:
			post_data (dict): Raw board post data.
		"""
		pass

	@staticmethod
	def _thumbnail_url(post_data):
		"""Construct the thumbnail url.
		
		Args:
			post_data (dict): Raw board post data.
		"""
		pass

	@staticmethod
	def _sample_url(post_data):
		"""Construct the sample url.
		
		Args:
			post_data (dict): Raw board post data.
		"""
		pass

	@classmethod
	def get_posts(cls):
		"""Retrieve the latest images."""
		return cls.search([])

	@classmethod
	def search(cls, tags, page=0):
		"""Get a list of image informations.

		Args:
			tags (list): A list of tags.
			page (int): Page to retrieve.
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
