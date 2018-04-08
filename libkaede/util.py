import requests
from . import WORKER_POOL


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
		self.progress = 0.

	def load(self, async=True):
		"""Load the image.

		Args:
			async (bool): Load asynchronously.
		"""
		if async:
			global WORKER_POOL
			WORKER_POOL.apply_async(self._loader)
		else:
			self._loader()

	def _loader(self):
		"""Load the image synchronously."""
		data_stream = requests.get(self.url, stream=True).raw
		self.size = data_stream.getheader('Content-Length')
		for data in data_stream.stream(decode_content=True):
			if data:
				self.buffer.extend(data)
			if self.size is not None:
				self.progress = data_stream.tell() / int(self.size)

	def unload(self):
		"""Remove the image from memory."""
		self.bytes = b''

	def save(self, folder, filename=None, async=True):
		"""Save the image to disk.

		Args:
			folder (str): Where to save.
			filename (str): How to name.
			async (bool): Save asynchronously.
		"""
		if async:
			global WORKER_POOL
			WORKER_POOL.apply_async(self._save, (folder, filename))
		else:
			self._savefolder, filename)

	def _save(self, folder, filename):
		"""Save the image to disk syncronously.
		
		Args:
			folder (str): Where to save.
			filename (str): How to name.
		"""
		if filename is None:
			filename = self.url.split('/')[-1]
		with open(folder+filename, 'wb') as output_file:
			output_file.write(self.buffer)
			# TODO Continue saving if buffer is not full
			# TODO Load if not loaded before
