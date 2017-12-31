#!/usr/bin/python3
import config
import boards
import errno
from threading import Thread, Event as threadingEvent
import os
import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GdkPixbuf, GLib


class StopableThread(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, *, daemon=None, owner=None):
        super(StopableThread, self).__init__(group=group, target=target,
                                             name=name, args=args,
                                             kwargs=kwargs, daemon=daemon)
        self._stop_event = threadingEvent()
        self.owner = owner

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class SearchThread(StopableThread):
    ''' Image search worker '''

    def __init__(self, owner):
        super(SearchThread, self).__init__(target=self.run, owner=owner)

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


class ImageLoadThread(StopableThread):
    def run(self):
        image_data = boards.TbibProvider().get_image(self.owner.data)
        if not self.stopped():
            pixbuf_loader = GdkPixbuf.PixbufLoader.new()
            pixbuf_loader.write(image_data)

            pixbuf = pixbuf_loader.get_pixbuf()
            pixbuf_loader.close()

            if pixbuf is None:
                return
            self.owner.pixbuf = pixbuf

            Gdk.threads_enter()
            self.owner.image_widget.queue_draw()
            Gdk.threads_leave()


class SaveImageThread(StopableThread):
    def __init__(self, *args, path, pixbuf):
        super(SaveImageThread, self).__init__(*args)
        self.path = path
        self.pixbuf = pixbuf

    def run(self):
        image_save_format = self.path.split('.')[-1]
        if image_save_format == "jpg":
            image_save_format = "jpeg"
        save_dir = os.path.dirname(self.path)

        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

        try:
            self.pixbuf.savev(self.path, image_save_format, "", "")
        except GLib.GError as exception:
            if exception.code == GdkPixbuf.PixbufError.UNSUPPORTED_OPERATION:
                print("Saving animations is currently unsupported, " +
                      "saving as PNG instead.")
                self.pixbuf.savev(self.path + '.png', "png", "", "")
            else:
                raise
