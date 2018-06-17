"""Board browsing helper.

Usage:
	1. Create a BoardProvider instance:
		BoardProvider is an abstract class to implement the comunication with
		boards. There are the following implementations included:
		- GelbooruProvider
		- TbibProvider

	2. Create a PostManager instance:
		Our PostManager instance will retrieve a bunch of posts from the board
		we're interacting with the BoardProvider

	3. Search or get a list of recent posts:
		The PostManager instance we crated can be called to search or list
		posts. As arguments, it can receive a string, a list or None.

	4. Process the data:
		To use the posts retrieved, you can iterate over the PostManager
		instance or get the items by id using `postManagerInstance['post id']`,
		where the post id must be an string.
"""

from multiprocessing.pool import ThreadPool
import gi
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GLib', '2.0')
gi.require_version('Gio', '2.0')


WORKER_POOL = ThreadPool()

from .__version__ import __title__, __version__, __description__, __url__, __author__, __author_email__, __license__, __copyright__
from .boards import *
from .posts import *
