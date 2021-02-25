#!/usr/bin/python3
import requests
import os.path


class Image():
	"""Image object.
	
	:param url: Where the image is located.
	:type url: str

	:cvar url: Image uri
	:vartype url: str

	:ivar buffer: Image bytes
	:vartype buffer: bytearray

	:ivar size: Image size in bytes
	:vartype size: int

	:ivar progress: Download progress
	:vartype progress: float
	"""

	def __init__(self, url):
		"""Init function.

		Args:
			url (str): Where the image is located.
		"""
		self.url = url
		self.buffer = bytearray()
		self.size = 0
		self.progress = 0.

	def load(self):
		"""Load the image on memory.
		
		:raises RuntimeError: if the image is already loaded.
		:raises ValueError: if the lenght of the image is unknown and the image
		                    cannot be loaded.
		"""
		if self.size > 0:
			raise RuntimeError('Image already loaded.')

		data_stream = requests.get(self.url, stream=True).raw
		length = data_stream.getheader('Content-Length')
		self.size = int(length if length is not None else 0)

		if self.size <= 0:
			raise ValueError('Unable to load the image: Network error')
		
		for data in data_stream.stream(decode_content=True):
			if data:
				self.buffer.extend(data)
				self.progress = data_stream.tell() / self.size

	def unload(self):
		"""Remove the image from memory."""
		self.buffer = bytearray()
		self.size = 0
		self.progress = 0.

	def save(self, folder, filename=None):
		"""Save the image to disk.

		:param folder: Where to save.
		:type folder: str
		:param filename: How to name.
		:type filename: str
		"""
		if filename is None:
			filename = self.url.split('/')[-1]
		with open(os.path.join(folder, filename), 'wb') as output_file:
			output_file.write(self.buffer)
			# TODO Continue saving if buffer is not full
			# TODO Load if not loaded before
			# TODO Thread safety
