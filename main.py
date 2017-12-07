#!/usr/bin/python3
import gi,requests
gi.require_version( 'Gtk', '3.0' )
from gi.repository import Gtk
from PIL import Image
from io import BytesIO

def on_button_clicked( widget ):
	print("Hi Boi!! <3")

def do_search( widget ):
	data = search( widget.get_text().split( ' ' ) )
	for item in data:
		image_byte_stream = BytesIO( get_image(item) )
		image = Image.open( image_byte_stream )
		image.save( item['image'] )

def _url( key, data = None ):
	tail = { 
			'list'     : "&s=post",
			'comments' : "&s=comment",
			}
	return "http://tbib.org/index.php?page=dapi&json=1" + "&q=index" + tail[ key ] + "&" + str(data)

def _image_url(post_data):
	return "http://tbib.org//images/" + post_data['directory'] + '/' + post_data['image']

def get_posts():
	return requests.get( _url('list') ).json()

def get_image(post_data):
	return requests.get( _image_url(post_data) ).content

def search(tags):
	tag_string = "tags=" + '+'.join(tags)
	response = requests.get( _url( 'list', tag_string ) )
	result = []
	print(response.content)
	if( response.content ):
		result = response.json()
	return result


if __name__ == '__main__':
	builder = Gtk.Builder()
	builder.add_from_file("main_window_ui.glade")
	win = builder.get_object("window1")
	win.set_title("Hello boi!!" )
	win.connect( 'delete-event', Gtk.main_quit )

	inputter = builder.get_object("entry1")
	inputter.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "system-search-symbolic")
	inputter.connect( "activate", do_search )

	vuvutton = builder.get_object("button1")
	vuvutton.set_label('Click Me! <3' )
	vuvutton.connect( "clicked", on_button_clicked )

	win.show_all()

	Gtk.main()
