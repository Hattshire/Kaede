#!/usr/bin/python3
'''Visualize pictures from imageboards'''
__version__ = '0.1.0a0'
import gi
gi.require_versions({
	'Gtk': '3.0', 'Gio': '2.0',
	'Gdk': '3.0', 'GdkPixbuf': '2.0'
})