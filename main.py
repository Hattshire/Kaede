#!/usr/bin/python3
import gi,requests
gi.require_version( 'Gtk', '3.0' )
from gi.repository import Gtk, Gdk, GdkPixbuf
from PIL import Image
from threading import Thread, Event as threadingEvent

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
		popup_window = ImageWindow(self.pixbuf, data)
		popup_window.show_all()

class SearchThread(Thread):
	def __init__(self,results_container,):
	    super(SearchThread, self).__init__()
	    self.results_container = results_container
	    self._stop_event = threadingEvent()

	def search(self,tags):
		self.clear_layout()
		self.tags = tags

	def run(self):
		self.add_results(self.results_container, self.tags)

	def add_results( self, container, tags):
		data = search( tags )
		width, height = container.get_size()
		y = 0
		x = 0
		for item in data:
			if(self.stopped()):
				return
			image_data = get_thumbnail(item)
			if(self.stopped()):
				return
			pixbuf_loader = GdkPixbuf.PixbufLoader.new()
			pixbuf_loader.write(image_data)

			image_pixbuf = pixbuf_loader.get_pixbuf()
			pixbuf_loader.close()
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

	def stop(self):
		self._stop_event.set()
	def stopped(self):
		return self._stop_event.is_set()

	def clear_layout(self):
		self.results_container.do_forall(self.results_container,False,self.remove_callback,None)
		self.results_container.set_size(self.results_container.get_allocated_width(),self.results_container.get_allocated_height())

	def remove_callback(self,widget,data):
		widget.destroy()

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
		self.inputter.connect( "activate", self.do_search )

		self.search_thread = SearchThread(self.layyout)

	def do_search( self, widget ):
		if(self.search_thread.ident != None):
			if(self.search_thread.is_alive()):
				self.search_thread.stop()
				self.search_thread.join(0.5)
			self.search_thread = SearchThread(self.layyout)
		self.search_thread.search(widget.get_text().split( ' ' ))
		self.search_thread.start()

	def show_all(self):
		self.window.show_all()

class ImageWindow(Gtk.Window):
	def __init__(self,pixbuf=None, data=None):
		super(ImageWindow,self).__init__()
		self.pixbuf = pixbuf
		self.data = data
		self.set_default_size( data["width"], data["height"])

		self.image_widget = Gtk.DrawingArea()
		self.image_widget.connect("draw", self.image_widget_draw,self.pixbuf)
		self.image_widget.set_hexpand(True)
		self.image_widget.set_vexpand(True)

		self.image_widget_container = Gtk.Grid()
		self.image_widget_container.attach(self.image_widget,0,0,1,1)
		self.connect("button_press_event",self.image_widget_click,self.data)
		self.add(self.image_widget_container)

		Thread(target=self.load_image).start()

	def image_widget_draw(self,widget,cairo_context,pixbuf):
		width = widget.get_allocated_width()
		height = widget.get_allocated_height()

		if(width / height > pixbuf.get_width() / pixbuf.get_height()):
			width = (height / pixbuf.get_height()) * pixbuf.get_width()
		elif (width / height < pixbuf.get_width() / pixbuf.get_height()):
			height = (width / pixbuf.get_width()) * pixbuf.get_height()

		scaled_pixbuf = pixbuf.scale_simple(width,height,GdkPixbuf.InterpType.BILINEAR)
		if(scaled_pixbuf == None):
			return

		x_offset = (widget.get_allocated_width() - width)//2
		y_offset = (widget.get_allocated_height() - height)//2

		Gdk.cairo_set_source_pixbuf(cairo_context,scaled_pixbuf,x_offset,y_offset)
		cairo_context.paint()

	def image_widget_click(self, widget,event_button,data):
		self.pixbuf.savev(data["image"]+".png","png","","")

	def load_image(self):
		image_data = get_image(self.data)

		pixbuf_loader = GdkPixbuf.PixbufLoader.new()
		pixbuf_loader.write(image_data)
		pixbuf = pixbuf_loader.get_pixbuf()
		pixbuf_loader.close()

		if(pixbuf == None):
			return
		self.pixbuf = pixbuf

		Gdk.threads_enter()
		self.image_widget.connect("draw", self.image_widget_draw,self.pixbuf)
		self.image_widget.queue_draw()
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
	builder.do_search(builder.inputter)

	Gdk.threads_init()
	Gdk.threads_enter()
	Gtk.main()
	Gdk.threads_leave()
