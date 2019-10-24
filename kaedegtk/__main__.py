#!/usr/bin/python3
'''Visualize pictures from imageboards'''
import gi
gi.require_versions({
	'Gtk': '3.0', 'Gio': '2.0',
	'Gdk': '3.0', 'GdkPixbuf': '2.0'
})
from gi.repository import Gtk, GdkPixbuf
import threading
import kaede

BACKEND = {"name": "NO_DEFAULT_BACKEND", "class": None}


def setBackend(backend_name):
	if backend_name != BACKEND['name'] and backend_name in kaede.board_providers:
		BACKEND['name'] = backend_name
		BACKEND['class'] = kaede.board_providers[backend_name]
		return True
	return False


if not setBackend(BACKEND['name']):
	BACKEND['name'], BACKEND['class'] = list(kaede.board_providers.items())[0]


def loadImage(widget, dest):
	tags = widget.props.text.strip().split()
	post = next(BACKEND['class'].search(tags, 0))
	post['image'].load()
	buffer = post['image'].buffer
	loader = GdkPixbuf.PixbufLoader.new()
	loader.write(buffer)
	loader.close()

	anim = loader.get_animation()
	if not anim:
		return

	if anim.is_static_image():
		dest.set_from_pixbuf(anim.get_static_image())
	else:
		dest.set_from_animation(anim)


def loadImageAsyncSignal(widget, dest):
	threading.Thread(target=loadImage, args=(widget, dest)).start()
	return True


def onBoardComboboxChange(widget, img):
	board_id = widget.get_active_id()
	if setBackend(board_id):
		img.clear()


def onAppActivate(app):
	WINDOW_TITLE = "Kaede"
	titlebar = Gtk.HeaderBar.new()
	titlebar.set_title(WINDOW_TITLE)
	titlebar.set_show_close_button(True)

	window = Gtk.ApplicationWindow.new(app)
	window.set_title(WINDOW_TITLE)
	window.set_default_size(420, 200)
	window.set_position(Gtk.WindowPosition.CENTER)
	window.set_titlebar(titlebar)

	img = Gtk.Image.new()
	tag_entry = Gtk.SearchEntry.new()
	tag_entry.connect('activate', loadImageAsyncSignal, img)

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
	board_combobox.connect('changed', onBoardComboboxChange, img)

	menu_button = Gtk.MenuButton.new()
	menu_button.set_image(Gtk.Image.new_from_icon_name('open-menu-symbolic',
	                                                   Gtk.IconSize.BUTTON))
	start_menu_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
	start_menu_box.add(menu_button)
	start_menu_box.add(board_combobox)
	titlebar.add(start_menu_box)

	titlebar.set_custom_title(tag_entry)
	window.add(img)
	window.show_all()


# App main loop/excecution
KaedeGtkApp = Gtk.Application.new("moe.hattshire.kaede", 0)
KaedeGtkApp.connect('activate', onAppActivate)
KaedeGtkApp.run()
