#!/usr/bin/python3
'''Visualize pictures from imageboards'''
__version__ = '0.1.0a0'
import gi
gi.require_versions({
  'Gtk': '3.0', 'Gio': '2.0',
  'Gdk': '3.0', 'GdkPixbuf': '2.0'
})
from gi.repository import Gtk, Gio, Gdk, GdkPixbuf


KaedeGtkApp = Gtk.Application.new("moe.hattshire.kaede", 0)

TITLE = "Kaede"
BACKEND = "Tbib"

titlebar = Gtk.HeaderBar.new()
titlebar.set_title(TITLE)
titlebar.set_show_close_button(True);
titlebar.set_subtitle(BACKEND)

def onAppActivate(app):
	window = Gtk.ApplicationWindow.new(app)
	window.set_title(TITLE)
	window.set_default_size(320, 200)
	window.set_position(Gtk.WindowPosition.CENTER)
	window.set_titlebar(titlebar)
	window.add(Gtk.Label.new(BACKEND))
	window.show_all()

KaedeGtkApp.connect('activate', onAppActivate)

KaedeGtkApp.run()

