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
		"""Save the image to disk asynchronously.

		Args:
			folder (str): Where to save.
			filename (str): How to name.
		"""
		global WORKER_POOL
		WORKER_POOL.apply_async(self._save, (folder, filename))

	def _save(self, folder, filename):
		"""Save the image to disk.
		
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
