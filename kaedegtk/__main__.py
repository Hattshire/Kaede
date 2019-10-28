#!/usr/bin/python3
'''Visualize pictures from imageboards'''
import gi
gi.require_versions({
	'Gtk': '3.0', 'Gio': '2.0',
	'Gdk': '3.0', 'GdkPixbuf': '2.0'
})
from gi.repository import Gtk, GdkPixbuf, GLib
import time
import threading
import kaede

BACKEND = {"name": "NO_DEFAULT_BACKEND", "class": None}


class StoppableLoopThread(threading.Thread):
	''' A Thread that loops a function and handles the thread state lock
	    on each loop. For cpu intensive things use multiprocessing instead.

	    WARNING:
	    Instead of overriding self.run, define self.target

	    TODO Handle _shutdown waiting behaviour
	'''
	def run(self):
		''' Loop until stop is called. '''
		while not self._is_stopped:
			if self._target is not None:
				self._target(*self._args, **self._kwargs)
			else:
				self.target()
			self._tstate_lock.release()
			# Wait 100ms so self._wait_for_tstate_lock can acquire the lock
			time.sleep(.1)
			if self._tstate_lock is None:
				return  # Sometimes the lock is cleared too quickly
			self._tstate_lock.acquire()
		# Implementation may expect to find this set to False
		self._is_stopped = False

	def target(self):
		''' Default target, just stops the thread loop. '''
		self._is_stopped = True
	
	def stop(self, block=True):
		'''Try to stop the thread gracefully '''
		# When it acquires the lock, sets automatically _is_stopped
		self._wait_for_tstate_lock(block=block)


class WallFillThread(StoppableLoopThread):
	''' A thread that fills the wall with thumbnails.
		Must be initialized specifying a container.

		Start it with .start() only once
		Reset/restart it with .reset()
		Set the search tags with .set_tags([tags]), it resets the wall by itself
		Continue filling with more()
	'''
	def __init__(self, *args, **keywords):
		self.container = keywords['container']
		self._tags = []
		self._runSignal = threading.Event()
		self._stop_ = False 
		del(keywords['container'])
		# This is a daemon
		keywords['daemon'] = True
		super().__init__(*args, **keywords)

		self.page = 0

	def _fillBox(self):
		''' Get posts from backend and create thumbnail widgetss on container. '''
		posts = BACKEND['class'].search(self._tags, self.page)
		for image in getThumbnailWidgetsFromPosts(posts):
			if self._stop_ or self._is_stopped:
				break
			self.container.add(image)
		self._stop_ = 'finished' if self._stop_ is False else self._stop_

	def _destroyContainerChildren(self):
		''' Destroy all widgets on container '''
		def destroyWidget(widget):
			widget.destroy()
		self.container.foreach(destroyWidget)

	def target(self):
		''' Handle the behaviour of the thread '''
		self._runSignal.clear()
		self._stop_ = False
		try:
			self._fillBox()
		except Exception as e:
			print("An exception ocurred while filling the wall: \n", e)

		self._runSignal.wait()
		self._runSignal.clear()
		if self._stop_ == 'reset':
			self._destroyContainerChildren()
			self.page = 0

	def stop(self, block=True):
		self._stop_ = 'stop'
		self._runSignal.set()
		super().stop(block)

	# ---------

	def reset(self):
		''' Send a reset hint to the thread. '''
		self._stop_ = 'reset'
		self._runSignal.set()

	def more(self):
		''' Tell the thread to load another page. '''
		self.page += 1
		self._runSignal.set()

	def set_tags(self, tags):
		''' Reset wall using specified tags. '''
		self._tags = tags
		self.reset()


def setBackend(backend_name):
	''' Change the currently used backend. '''
	if backend_name != BACKEND['name'] and backend_name in kaede.board_providers:
		BACKEND['name'] = backend_name
		BACKEND['class'] = kaede.board_providers[backend_name]
		return True
	return False


# Set the default backend as the first backend found
if not setBackend(BACKEND['name']):
	BACKEND['name'], BACKEND['class'] = list(kaede.board_providers.items())[0]


def getPixbufAniFromImage(image):
	''' Generates a GdkPixbufAnimation from a given KaedeImage. '''
	loader = GdkPixbuf.PixbufLoader.new()
	try:
		image.load()
		buffer = image.buffer
		loader.write(buffer)
	finally:
		try:
			loader.close()
		except GLib.GError:
			return None
	return loader.get_animation()


def setImageFromPixbufAni(anim, dest):
	''' Sets the correct content of a GtkImage from a GdkPixbufAnimation. '''
	if anim.is_static_image():
		dest.set_from_pixbuf(anim.get_static_image())
	else:
		dest.set_from_animation(anim)


def getThumbnailWidgetsFromPosts(posts):
	''' Yield GtkImage widgets from a KaedePost list. '''
	for post in posts:
		pixbuf = getPixbufAniFromImage(post['thumbnail'])
		if not pixbuf:
			continue
		image = Gtk.Image.new()
		image.show()
		setImageFromPixbufAni(pixbuf, image)
		yield image


def onBoardComboboxChange(widget, thread):
	''' Reset wall when the board changes. '''
	board_id = widget.get_active_id()
	if setBackend(board_id):
		thread.reset()
	# TODO Reset widget's active when setBackend fails


def onTagEntry(widget, thread):
	''' Change tags when TagEntry gets activated. '''
	tags = widget.props.text.strip().split()
	thread.set_tags(tags)


def onAppActivate(app):
	WINDOW_TITLE = "Kaede"
	titlebar = Gtk.HeaderBar.new()
	titlebar.set_title(WINDOW_TITLE)
	titlebar.set_show_close_button(True)

	window = Gtk.ApplicationWindow.new(app)
	window.set_title(WINDOW_TITLE)
	window.set_default_size(600, 400)
	window.set_position(Gtk.WindowPosition.CENTER)
	window.set_titlebar(titlebar)

	wall_container = Gtk.FlowBox.new()
	wall_container.set_orientation(Gtk.Orientation.VERTICAL)

	fillthread = WallFillThread(container=wall_container)
	fillthread.start()

	tag_entry = Gtk.SearchEntry.new()
	tag_entry.connect('activate', onTagEntry, fillthread)

	# Generate a list of boards to display
	board_list = Gtk.ListStore(str)
	for board_name in kaede.board_providers.keys():
		board_list.append([board_name])

	board_combobox = Gtk.ComboBox.new_with_model(board_list)
	board_text_renderer = Gtk.CellRendererText()
	board_combobox.pack_start(board_text_renderer, True)
	board_combobox.add_attribute(board_text_renderer, "text", 0)
	board_combobox.set_id_column(0)
	board_combobox.set_active_id(BACKEND['name'])
	board_combobox.connect('changed', onBoardComboboxChange, fillthread)

	menu_button = Gtk.MenuButton.new()
	menu_button.set_image(Gtk.Image.new_from_icon_name('open-menu-symbolic',
	                                                   Gtk.IconSize.BUTTON))
	start_menu_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
	start_menu_box.add(menu_button)
	start_menu_box.add(board_combobox)
	titlebar.add(start_menu_box)

	titlebar.set_custom_title(tag_entry)
	scrolled_wall = Gtk.ScrolledWindow.new()
	scrolled_wall.add(wall_container)
	window.add(scrolled_wall)
	window.show_all()


# App main loop/excecution
KaedeGtkApp = Gtk.Application.new("moe.hattshire.kaede", 0)
KaedeGtkApp.connect('activate', onAppActivate)
KaedeGtkApp.run()
