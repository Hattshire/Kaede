#!/usr/bin/python3
'''Visualize pictures from imageboards'''
from gi.repository import Gtk
from .util import Wall, BackendSwitch


def onTagEntry(widget, container):
	''' Change tags when TagEntry gets activated. '''
	tags = widget.props.text.strip().split()
	container.reset_with_tags(tags)


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

	board_combobox = BackendSwitch()
	tag_entry = Gtk.SearchEntry.new()
	wall = Wall(orientation=Gtk.Orientation.VERTICAL, homogeneous=True)

	tag_entry.connect('activate', onTagEntry, wall)
	board_combobox.connect('changed', board_combobox.onChanged, wall)

	menu_button = Gtk.MenuButton.new()
	menu_button.set_image(Gtk.Image.new_from_icon_name('open-menu-symbolic',
	                                                   Gtk.IconSize.BUTTON))
	start_menu_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
	start_menu_box.add(menu_button)
	start_menu_box.add(board_combobox)
	titlebar.add(start_menu_box)

	titlebar.set_custom_title(tag_entry)
	scrolled_wall = Gtk.ScrolledWindow.new()
	# TODO use vertical wheel scroll on horizontal scroll of the
	# vertical-aligned wall
	scrolled_wall.add(wall)
	window.add(scrolled_wall)
	window.show_all()


# App main loop/excecution
KaedeGtkApp = Gtk.Application.new("moe.hattshire.kaede", 0)
KaedeGtkApp.connect('activate', onAppActivate)
KaedeGtkApp.run()
