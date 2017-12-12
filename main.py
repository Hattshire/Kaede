#!/usr/bin/python3
import gi,requests
gi.require_version( 'Gtk', '3.0' )
from gi.repository import Gtk, Gdk, GdkPixbuf
from PIL import Image
from io import BytesIO
from threading import Thread

class ImageWidget(Gtk.EventBox):
	def __init__(self, pixbuf, item_data):
		super(ImageWidget, self).__init__()
		if(pixbuf == None):
			return None

		self.pixbuf = pixbuf
		self.image = Gtk.Image.new_from_pixbuf(self.pixbuf)
		self.image.show()
		self.add(self.image)
		self.connect("button_press_event",self.image_on_click,item_data)

	def image_on_click(self, widget,event_button,data):
		popup_window = ImageWindow()
		Thread(target=popup_window.ioc_thread,args=[popup_window,data]).start()

class MainWindow(Gtk.Builder):
	def __init__(self):
		super(MainWindow, self).__init__()
		self.add_from_file("main_window_ui.glade")
		self.window = self.get_object("window1")
		self.window.set_title("Hello boi!!" )
		self.window.connect( 'delete-event', Gtk.main_quit )

		self.layyout = self.get_object("layout1")

		self.inputter = self.get_object("entry1")
		self.inputter.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "system-search-symbolic")
		self.inputter.connect( "activate", self.do_search, self.layyout )

	def do_search( self, widget, container ):
		Thread(target=self.add_results,args=[container,widget.get_text().split( ' ' )]).start()

	def add_results( self, container, tags):
		data = search( tags )
		width, height = container.get_size()
		y = 0
		x = 0
		for item in data:
			image_data = get_thumbnail(item)
			pixbuf_loader = GdkPixbuf.PixbufLoader.new()
			pixbuf_loader.write(image_data)

			image_pixbuf = pixbuf_loader.get_pixbuf()
			if(image_pixbuf == None):
				continue

			image_event_widget = ImageWidget(image_pixbuf, item)
			image_event_widget.show()

			if (y+image_pixbuf.get_height() > height):
				y = 0
				x += 160
			Gdk.threads_enter()
			if (x+160 > width):
				width += 160
				container.set_size(width,height,)
			container.put(image_event_widget,x,y)
			Gdk.threads_leave()
			y += image_pixbuf.get_height()

	def show_all(self):
		self.window.show_all()

class ImageWindow(Gtk.Window):
	def image_widget_draw(self,widget,cairo_context,pixbuf):
		width = widget.get_allocated_width()
		height = widget.get_allocated_height()
		scaled_pixbuf = pixbuf.scale_simple(width,height,GdkPixbuf.InterpType.BILINEAR)
		Gdk.cairo_set_source_pixbuf(cairo_context,scaled_pixbuf,0,0)
		cairo_context.paint()

	def ioc_thread(self, popup_window,data):
		image_data = get_image(data)
		pixbuf_loader = GdkPixbuf.PixbufLoader.new()
		pixbuf_loader.write(image_data)
		image_pixbuf = pixbuf_loader.get_pixbuf()
		if(image_pixbuf == None):
			return
		image_widget = Gtk.DrawingArea()
		image_widget.set_hexpand(True)
		image_widget.set_vexpand(True)
		image_widget.connect("draw", self.image_widget_draw,image_pixbuf)
		image_widget_container = Gtk.Grid()
		image_widget_container.attach(image_widget,0,0,1,1)
		Gdk.threads_enter()
		popup_window.set_default_size( image_pixbuf.get_width(), image_pixbuf.get_height())
		popup_window.add(image_widget_container)
		popup_window.show_all()
		Gdk.threads_leave()





def _url( key, data = None ):
	tail = { 
			'list'     : "&s=post",
			'comments' : "&s=comment",
			}
	return "http://tbib.org/index.php?page=dapi&json=1" + "&q=index" + tail[ key ] + "&" + str(data)

def _image_url(post_data):
	return "http://tbib.org//images/" + post_data['directory'] + '/' + post_data['image']

def _thumbnail_url(post_data):
	return "http://tbib.org/thumbnails/" + post_data['directory'] + '/thumbnail_' + post_data['image']

def get_posts():
	return requests.get( _url('list') ).json()

def get_image(post_data):
	return requests.get( _image_url(post_data) ).content

def get_thumbnail(post_data):
	return requests.get( _thumbnail_url(post_data) ).content

def search(tags):
	tag_string = "tags=" + '+'.join(tags)
	response = requests.get( _url( 'list', tag_string ) )
	result = []
	if( response.content ):
		result = response.json()
	return result


if __name__ == '__main__':
	builder = MainWindow()

	builder.show_all()

	Gdk.threads_init()
	Gdk.threads_enter()
	Gtk.main()
	Gdk.threads_leave()
