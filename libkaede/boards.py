import requests


class BoardProvider():
	"""Base for a imageboard provider."""
	#TODO: Don't use self|Make it static

	def _list_url(self, tags=None, page=0):
		"""Construct the post listing url.
		
		Args:
			tags (list|str|None): Keywords to search for.
			page (int): Search page to show.
		"""
		pass

	def _image_url(self, post_data):
		"""Construct the image url.
		
		Args:
			post_data (dict): Raw board post data.
		"""
		pass

	def _thumbnail_url(self, post_data):
		"""Construct the thumbnail url.
		
		Args:
			post_data (dict): Raw board post data.
		"""
		pass

	def _sample_url(self, post_data):
		"""Construct the sample url.
		
		Args:
			post_data (dict): Raw board post data.
		"""
		pass

	def get_posts(self):
		"""Retrieve the latest images."""
		return requests.get(self._url('list')).json()

	def get_image(self, post_data):
		"""Retrieve an image.

		Args:
			post_data (dict): Raw board post data.
		"""
		return requests.get(self._image_url(post_data)).content

	def get_thumbnail(self, post_data):
		"""Retrieve a thumbnail.

		Args:
			post_data (dict): Raw board post data.
		"""
		return requests.get(self._thumbnail_url(post_data)).content

	def search(self, tags, page=0):
		"""Get a list of image informations.

		Args:
			tags (list): A list of tags.
			page (int): Page to retrieve.
		"""
		tag_string = '+'.join(tags)
		response = requests.get(self._url(tag_string, page))
		result = []

		if(response.content):
			result = response.json()
		for item in result:
			if 'thumbnail_url' not in item:
				item['thumbnail_url'] = self._thumbnail_url(item)
			if 'image_url' not in item:
				item['image_url'] = self._image_url(item)
			if 'sample_url' not in item and 'sample' in item:
				item['sample_url'] = self._sample_url(item)
			yield item


class GelbooruProvider(BoardProvider):
	"""Board provider for Gelbooru."""

	def _list_url(self, tags=None, page=0):
		return "http://gelbooru.com/index.php?page=dapi&json=1&q=index" + \
			   "&s=post" + "&tags=" + str(tags) + "&pid=" + str(page)

	def _image_url(self, post_data):
		url = post_data['file_url']
		return url

	def _thumbnail_url(self, post_data):
		url = "http://simg3.gelbooru.com/thumbnails/" + \
			  post_data['directory'] + '/thumbnail_' + \
			  post_data['hash'] + '.jpg'
		return url

	def _sample_url(self, post_data):
		# TODO Implement sample urls for gelbooru
		return self._image_url(post_data)


class TbibProvider(BoardProvider):
	"""Board provider for The big image board."""

	def _list_url(self, tags=None, page=0):
		return "http://tbib.org/index.php?page=dapi&json=1&q=index" + \
			   "&s=post" + "&tags=" + str(tags) + "&pid=" + str(page)

	def _image_url(self, post_data):
		url = "http://tbib.org//images/" + \
			  post_data['directory'] + '/' + post_data['image']
		return url

	def _thumbnail_url(self, post_data):
		url = "http://tbib.org/thumbnails/" + \
			  post_data['directory'] + '/thumbnail_' + post_data['image']
		return url

	def _sample_url(self, post_data):
		# TODO Implement sample urls for tbib
		return self._image_url(post_data)
