#!/usr/bin/python3
import gi,requests
gi.require_version( 'Gtk', '3.0' )
from gi.repository import Gtk
from PIL import Image
from io import BytesIO

def on_button_clicked( widget ):
	print("Hi Boi!! <3")
	Image.open(BytesIO(get_image(search(["asdf",])[0]))).save("sample.jpg")

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
	return requests.get( _url( 'list', tag_string ) ).json()


if __name__ == '__main__':
	win = Gtk.Window( title="Hello boi!!" )
	win.connect( 'delete-event', Gtk.main_quit )

	box = Gtk.Box()

	inputter = Gtk.Entry()
	inputter.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "system-search-symbolic")
	inputter.connect( "activate", do_search )

	vuvutton = Gtk.Button( label='Click Me! <3' )
	vuvutton.connect( "clicked", on_button_clicked )

	box.pack_start(inputter, True, True, 0)
	box.pack_start(vuvutton, True, True, 0)

	win.add( box )
	win.show_all()

	Gtk.main()
