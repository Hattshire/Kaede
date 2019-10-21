#!/usr/bin/python3
"""Board browsing helper.

Usage:
	1. Create a Board instance:
		Board is an abstract class to implement the basic comunication with
		boards.
		Board providers can be found in the board_providers dict

	2. (Optional) Create a SearchHelper instance:
		The SearchHelper will cache posts in memory and hold the search terms.

	3. Search or get a list of recent posts:
		The SearchHelper instance we crated can be use to search posts.
		Also the Board instance can be used using it's `search` method.

	4. Process the data:
		Each Post has an `image` and a `thumbnail` along with it's `id` and `tags`

	For more info check the documentation for each class.
"""
from .boards import Board
from .posts import Post, SearchHelper
import pkg_resources as __pkgr

__version__ = '0.1.0a0'

board_providers = {}

for entry_point in __pkgr.iter_entry_points('kaede.boards_provider'):
	board_providers[entry_point.name] = entry_point.load()
