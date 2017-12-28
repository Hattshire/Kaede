#!/usr/bin/python3
from threading import Thread, Event as threadingEvent
import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GdkPixbuf
import config
import boards


class StopableThread(Thread):

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, *, daemon=None):
        super(StopableThread, self).__init__(group=group, target=target,
                                             name=name, args=args,
                                             kwargs=kwargs, daemon=daemon)
        self._stop_event = threadingEvent()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class SearchThread(StopableThread):
    ''' Image search worker '''

    def __init__(self, owner):
        super(SearchThread, self).__init__(target=self.run)
        self.owner = owner

    def search(self, tags, page=0):
        ratings = []
        for rating in ['safe', 'questionable', 'explicit']:
            if config.get_config(
                'Search settings', 'Rating ' + rating, "Enable"
            ) != "Enable":
                ratings.append("-rating:" + rating)

        self.tags = tags + ratings
        self.page = page

    def run(self):
        data = boards.TbibProvider().search(self.tags, self.page)
        for item in data:
            image_data = boards.TbibProvider().get_thumbnail(item)
            if(self.stopped()):
                return

            pixbuf_loader = GdkPixbuf.PixbufLoader.new()
            pixbuf_loader.write(image_data)

            item['thumbnail_pixbuf'] = pixbuf_loader.get_pixbuf()
            pixbuf_loader.close()

            if item['thumbnail_pixbuf'] is None:
                continue
            Gdk.threads_enter()
            self.owner.add_thumbnail(item)
            Gdk.threads_leave()
