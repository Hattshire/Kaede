#!/usr/bin/python3
from gi.repository import Gtk, GdkPixbuf, GLib, GObject
import time
import concurrent.futures
import kaede

global current_backend


class BackendSwitch(Gtk.ComboBox):
	def __init__(self, *args, board=None, **kwargs):
		super().__init__(*args, **kwargs)

		text_renderer = Gtk.CellRendererText()
		self.pack_start(text_renderer, True)
		self.add_attribute(text_renderer, "text", 0)

		# Generate a list of boards to display
		board_list = Gtk.ListStore(str)
		for board_name in kaede.board_providers.keys():
			board_list.append([board_name])
		self.set_model(board_list)
		self.set_id_column(0)

		# Set the default backend as the first backend found
		self.board = ""
		if not self.set(board):
			board = list(kaede.board_providers.keys())[0]
			self.set(board)

	def set(self, backend_name):
		''' Change the currently used backend. '''
		global current_backend
		if backend_name != self.board and backend_name in kaede.board_providers:
			self.board = backend_name
			current_backend = kaede.board_providers[backend_name]
			if not self.set_active_id(backend_name):
				self.set_active_id(None)
			return True
		self.set_active_id(None)
		return False

	def onChanged(self, widget, container):
		''' Reset wall when the board changes. '''
		board_id = widget.get_active_id()
		if self.set(board_id):
			container.reset()


class Image(Gtk.Image):
	def __init__(self, post=None, *args, **kwargs):
		self._post = post
		super().__init__(*args, **kwargs)

	def get_id(self):
		return self._post['id']

	def getPixbufAniFromImage(self):
		''' Generates a GdkPixbufAnimation from a given KaedeImage. '''
		image = self._post['thumbnail']
		loader = GdkPixbuf.PixbufLoader.new()
		try:
			image.load()
			buffer = image.buffer
			loader.write(buffer)
		except Exception as e:
			print("Exception while loading a some Image:", e)
		finally:
			try:
				loader.close()
			except GLib.GError as e:
				print("WARNING: Can't load image with id:", self.get_id())
				print(e)
				return None
		return loader.get_animation()

	def setImageFromPixbufAni(self, anim):
		''' Sets the correct content of a GtkImage from a GdkPixbufAnimation. '''
		if anim.is_static_image():
			self.set_from_pixbuf(anim.get_static_image())
		else:
			self.set_from_animation(anim)

	def load(self):
		try:
			pixbuf = self.getPixbufAniFromImage()
			if not pixbuf or pixbuf is None:
				self.set_from_icon_name(
					'dialog-error', Gtk.IconSize.DIALOG)
			else:
				self.setImageFromPixbufAni(pixbuf)
		except Exception as e:
			print(e)

	@classmethod
	def from_post(cls, post):
		''' Generate widget from a KaedePost. '''
		image = cls(post=post)
		return image


class Wall(Gtk.FlowBox):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.tags = []
		self.page = 0
		self._session_id = time.time_ns()
		self.contained_ids = []
		self._pending_futures = set()
		self._executor = concurrent.futures.ThreadPoolExecutor()
		self.set_sort_func(self.sort_function)
		self.fill()

	@GObject.Signal
	def append_pending(self, image: Image, session_id: object):
		# Don't Show/Add the image if the request is out of sync
		if session_id != self._session_id:
			return
		image.show()
		self.add(image)

	def reset(self, clear_tags=True):
		self.stop()
		if clear_tags:
			del self.tags
			self.tags = []
		del self.contained_ids
		self.contained_ids = []

		def destroyWidget(widget):
			widget.destroy()
		self.foreach(destroyWidget)

		self.fill()

	def reset_with_tags(self, tags):
		if self.set_tags(tags):
			self.reset(clear_tags=False)

	def set_tags(self, tags):
		if isinstance(tags, list):
			self.tags = tags
			return True
		return False

	def add_image_from_post(self, post):
		try:
			if post['id'] in self.contained_ids:
				raise Exception("Post beign displayed already")
			session_id = self._session_id
			image = Image.from_post(post)
			image.load()
			self.emit('append_pending', image, session_id)
			print("Image", post['id'], "loaded")
			self.contained_ids.append(post['id'])
		except Exception as e:
			print(e)

	def work_posts(self):
		global current_backend
		self._post_generator = current_backend.search(self.tags, self.page)
		for post in self._post_generator:
			self.execute(self.add_image_from_post, post)

	def fill(self):
		self.execute(self.work_posts)

	def execute(self, fn, *args, **kwargs):
		future = self._executor.submit(fn, *args, **kwargs)
		self._pending_futures.add(future)
		
		def delete_future(future):
			del future
		future.add_done_callback(delete_future)

	def stop(self, wait=False):
		self._executor.shutdown(wait=False)
		for task in self._pending_futures:
			task.cancel()
		self._session_id = time.time_ns()
		self._executor = concurrent.futures.ThreadPoolExecutor()

	def more(self):
		self.page += 1
		self.fill()

	def sort_function(self, child1, child2):
		return child2.get_child().get_id() - child1.get_child().get_id()
