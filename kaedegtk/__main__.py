#!/usr/bin/python3
'''Visualize pictures from imageboards'''
import gi
gi.require_versions({
	'Gtk': '3.0', 'Gio': '2.0',
	'Gdk': '3.0', 'GdkPixbuf': '2.0'
})
from gi.repository import Gtk, GdkPixbuf
import threading

KaedeGtkApp = Gtk.Application.new("moe.hattshire.kaede", 0)

TITLE = "Kaede"
BACKEND = "Tbib"

titlebar = Gtk.HeaderBar.new()
titlebar.set_title(TITLE)
titlebar.set_show_close_button(True)
titlebar.set_subtitle(BACKEND)


def onAppActivate(app):
	window = Gtk.ApplicationWindow.new(app)
	window.set_title(TITLE)
	window.set_default_size(320, 200)
	window.set_position(Gtk.WindowPosition.CENTER)
	window.set_titlebar(titlebar)

	box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
	img = Gtk.Image.new()
	imgsrc = Gtk.Entry.new()
	box.pack_start(imgsrc, True, True, 0)
	box.pack_start(img, True, True, 0)

	def loadImage(image, dest):
		buffer = bytes()
		with open(image, 'rb') as imf:
			buffer = imf.read()

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
		threading.Thread(target=loadImage, args=(widget.props.text, dest)).run()

	imgsrc.connect('activate', loadImageAsyncSignal, img)
	window.add(box)
	window.show_all()


KaedeGtkApp.connect('activate', onAppActivate)

KaedeGtkApp.run()
