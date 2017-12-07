#!/usr/bin/python3
import gi,requests
gi.require_version( 'Gtk', '3.0' )
from gi.repository import Gtk
from PIL import Image
from io import BytesIO

def on_button_clicked( widget ):
	print("Hi Boi!! <3")
	Image.open(BytesIO(get_image(get_posts()[0]))).save("sample.jpg")
	
def _url( key, data = None ):
	tail = { 
			'list'     : "&s=post",
			'comments' : "&s=comment",
			}
	return "http://tbib.org/index.php?page=dapi&json=1" + "&q=index" + tail[ key ]
def _image_url(post_data):
	return "http://tbib.org//images/" + post_data['directory'] + '/' + post_data['image']

def get_posts():
	return requests.get( _url('list') ).json()

def get_image(post_data):
	return requests.get( _image_url(post_data) ).content

def search(tags):
	pass

win = Gtk.Window( title="Hello boi!!" )
win.connect( 'delete-event', Gtk.main_quit )

vuvutton = Gtk.Button( label='Click Me! <3' )
vuvutton.connect( "clicked", on_button_clicked )

win.add( vuvutton )
win.show_all()

Gtk.main()
