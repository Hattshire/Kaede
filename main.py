#!/usr/bin/python3
import gi
gi.require_version('Gtk', '3.0')
import config
import boards
from gi.repository import Gtk, Gdk, GdkPixbuf
from threading import Thread, Event as threadingEvent


class ThumbnailWidget(Gtk.EventBox):
    ''' Widget for thumbnails '''

    def __init__(self, data):
        super(ThumbnailWidget, self).__init__()

        if(data['thumbnail_pixbuf'] is None):
            return None

        self.data = data
        self.image = Gtk.Image.new_from_pixbuf(self.data['thumbnail_pixbuf'])
        self.image.show()

        self.add(self.image)

    def image_on_click(self, widget, event_button, parent_window):
        popup_window = ImageWindow(self.data, parent_window)
        popup_window.show_all()

    def get_size(self):
        return self.data['thumbnail_pixbuf'].get_width(), \
            self.data['thumbnail_pixbuf'].get_height()


class SearchThread(Thread):
    ''' Image search worker '''

    def __init__(self, owner):
        super(SearchThread, self).__init__()
        self.owner = owner
        self._stop_event = threadingEvent()

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

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super(MainWindow, self).__init__(application=app)
        self.set_title("Kaede")
        self.connect("size-allocate", self.update_on_resize)

        self.size = {'height': 0, 'width': 0}

        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/main_window_layout.glade")
        self.builder.add_from_file("ui/headerbar_menu.glade")
        self.builder.add_from_file("ui/headerbar_layout.glade")

        content = self.builder.get_object('window-content')
        headerbar = self.builder.get_object('main-headerbar')
        self.add(content)
        self.set_titlebar(headerbar)

        content.connect("scroll-event", self.wall_scroll)
        content.connect("edge-reached", self.overscroll)

        self.thumbnails = {
            'container': self.builder.get_object("window-layout"),
            'last-x': 0,
            'last-y': 0,
            'y-offset': 0,
            'data': [],
            'page': 0
        }

        self.search_input = self.builder.get_object("tag-search-entry")

        self.search_input.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, "system-search-symbolic")

        self.search_input.connect("activate", self.do_search)
        self.search_tags = None
        self.search_thread = SearchThread(self)

        self.config_fields = \
            {'rating': {
                'safe':
                self.builder.get_object("switch-rating-safe"),

                'questionable':
                self.builder.get_object("switch-rating-questionable"),

                'explicit':
                self.builder.get_object("switch-rating-explicit")
            }
            }
        for switch_name, switch_object in self.config_fields['rating'].items():
            rating = switch_name
            switch_object.set_active(
                config.get_config(
                    'Search settings', 'Rating ' + rating, "Enable"
                ) == "Enable"
            )
            switch_object.connect("notify::active", self.rating_config)

    def wall_scroll(self, widget, scroll_event):
        hadj = widget.get_hadjustment()
        hadj.set_value(hadj.get_value() +
                       scroll_event.delta_y * hadj.get_step_increment())

    def overscroll(self, widget, pos):
        if pos is Gtk.PositionType.RIGHT and not self.search_thread.is_alive():
            self.do_search(None, True)

    def rating_config(self, button, active):
        rating = Gtk.Buildable.get_name(button).split('-')[2]
        if button.get_active():
            config.set_config('Search settings', 'Rating ' + rating, "Enable")
        else:
            config.set_config('Search settings', 'Rating ' + rating, "Disable")
        self.do_search(None)

    def update_on_resize(self, widget, allocation):
        if allocation.width != self.size['width']:
            self.size['width'] = allocation.width

        if allocation.height != self.size['height']:
            self.size['height'] = allocation.height
            self.clear_layout()
            self.thumbnails['y-offset'] = \
                (self.thumbnails['container'].get_size().height % 160) // 2
            for item in self.thumbnails['data']:
                self.do_add_thumbnail(item)

    def add_thumbnail(self, data):
        # Add the thumbnail only if it wasn't added before
        # to prevent repeated results
        if not [thumb for
                thumb in self.thumbnails['data'] if thumb["id"] == data["id"]]:
            self.thumbnails['data'].append(data)
            self.do_add_thumbnail(data)

    def do_add_thumbnail(self, data):
        x = self.thumbnails['last-x']
        y = self.thumbnails['last-y']

        width, height = self.thumbnails['container'].get_size()

        thumbnail_widget = ThumbnailWidget(data=data)
        thumbnail_widget.connect("button_press_event",
                                 thumbnail_widget.image_on_click,
                                 self)
        thumbnail_widget.show()
        thumb_width, thumb_height = thumbnail_widget.get_size()
        thumb_offset = {'x': (160 - thumb_width) // 2,
                        'y': (160 - thumb_height) // 2}

        if(y + 160 > height):
            y = 0
            x = self.thumbnails['last-x'] = x + 160
        if(x + 160 > width):
            width += 160
            self.thumbnails['container'].set_size(width, height)
        if y == 0:
            y = self.thumbnails['y-offset']
        self.thumbnails['last-y'] = y + 160
        self.thumbnails['container'].put(thumbnail_widget,
                                         x + thumb_offset['x'],
                                         y + thumb_offset['y'])

    def clear_layout(self):
        self.thumbnails['last-x'] = 0
        self.thumbnails['last-y'] = 0
        self.thumbnails['page'] = 0
        self.thumbnails['container'].do_forall(self.thumbnails['container'],
                                               False,
                                               self.remove_callback,
                                               None)
        self.thumbnails['container'].set_size(
            self.thumbnails['container'].get_allocated_width(),
            self.thumbnails['container'].get_allocated_height())

    def remove_callback(self, widget, data):
        widget.destroy()

    def do_search(self, widget, new_page=False):
        if not new_page:
            self.thumbnails['data'][:] = []
            if(self.search_thread.ident is not None):
                if(self.search_thread.is_alive()):
                    self.search_thread.stop()
                    self.search_thread.join(0.5)
            self.clear_layout()

        self.search_thread = SearchThread(self)
        if widget is not None:
            self.search_tags = widget.get_text()
        if(self.search_tags):
            self.set_title("Kaede - " + self.search_tags)
        self.search_thread.search(self.search_tags.split(' '),
                                  self.thumbnails['page'])
        self.search_thread.start()
        self.thumbnails['page'] += 1


class KaedeApplication(Gtk.Application):
    def __init__(self):
        super(KaedeApplication, self).__init__()
        self.app_window = None

    def do_activate(self):
        self.app_window = MainWindow(self)
        self.app_window.show_all()
        self.app_window.do_search(self.app_window.search_input)

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_shutdown(self):
        if(self.app_window.search_thread.is_alive()):
            self.app_window.search_thread.stop()
            self.app_window.search_thread.join(0.5)
        Gtk.Application.do_shutdown(self)


class ImageWindow(Gtk.Window):
    ''' To show the full-size image '''

    def __init__(self, data, parent_window=None):
        super(ImageWindow, self).__init__()
        self.builder = Gtk.Builder\
                          .new_from_file("ui/image_window_layout.glade")
        self.data = data
        self.pixbuf = data['thumbnail_pixbuf']
        self.parent_window = parent_window

        self.content = self.builder.get_object('window-content')
        self.headerbar = self.builder.get_object('image-headerbar')
        self.image_widget = self.builder.get_object('image-container')

        self.save_button = self.builder.get_object('button-save')
        self.prev_button = self.builder.get_object('button-prev')
        self.next_button = self.builder.get_object('button-next')
        self.close_button = self.builder.get_object('button-close')

        self.add(self.content)
        self.set_titlebar(self.headerbar)

        self.set_title(data['tags'])

        # Set window size proportionally to the image
        screen = self.get_screen()
        max_width, max_height = screen.get_width(), screen.get_height()

        if max_width < data['width']:
            width = max_width
        else:
            width = data['width']

        if max_height < data['height']:
            height = max_height
        else:
            height = data['height']

        if (width / height > data['width'] / data['height']):
            width = (height / data['height']) * data['width']
        elif(width / height < data['width'] / data['height']):
            height = (width / data['width']) * data['height']

        self.set_default_size(width, height)

        self.image_widget.connect("draw", self.image_widget_draw)

        self.save_button.connect('clicked', self.save_image, self.data)
        self.close_button.connect('clicked', self.close_window)

        if self.parent_window is None:
            self.prev_button.destroy()
            self.next_button.destroy()
        else:
            self.prev_button.connect('clicked', self.prev_image)
            self.next_button.connect('clicked', self.next_image)

        self.load_thread = Thread(target=self.load_image)
        self.load_thread.start()

    def close_window(self, widget):
        self.close()

    def next_image(self, widget):
        self.load_thread = Thread(target=self.load_image)
        self.load_thread.start()
        data = [thumb
                for thumb in self.parent_window.thumbnails['data']
                if thumb["id"] > self.data["id"]]
        if data:
            self.data = data[-1]
        else:
            return False
        self.pixbuf = self.data['thumbnail_pixbuf']
        self.image_widget.queue_draw()

    def prev_image(self, widget):
        self.load_thread = Thread(target=self.load_image)
        self.load_thread.start()
        data = [thumb
                for thumb in self.parent_window.thumbnails['data']
                if thumb["id"] < self.data["id"]]
        if data:
            self.data = data[0]
        else:
            return False
        self.pixbuf = self.data['thumbnail_pixbuf']
        self.image_widget.queue_draw()

    def image_widget_draw(self, widget, cairo_context):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        pixbuf = self.pixbuf

        if (width / height > pixbuf.get_width() / pixbuf.get_height()):
            width = (height / pixbuf.get_height()) * pixbuf.get_width()
        elif(width / height < pixbuf.get_width() / pixbuf.get_height()):
            height = (width / pixbuf.get_width()) * pixbuf.get_height()

        scaled_pixbuf = pixbuf.scale_simple(width, height,
                                            GdkPixbuf.InterpType.BILINEAR)
        if(scaled_pixbuf is None):
            return

        x_offset = (widget.get_allocated_width() - width) // 2
        y_offset = (widget.get_allocated_height() - height) // 2

        Gdk.cairo_set_source_pixbuf(cairo_context, scaled_pixbuf,
                                    x_offset, y_offset)
        cairo_context.paint()

    def save_image(self, widget, data):
        save_thread = Thread(target=self.pixbuf.savev,
                             args=[data["image"] + ".png", "png", "", ""])
        save_thread.start()

    def load_image(self):
        image_data = boards.TbibProvider().get_image(self.data)

        pixbuf_loader = GdkPixbuf.PixbufLoader.new()
        pixbuf_loader.write(image_data)

        pixbuf = pixbuf_loader.get_pixbuf()
        pixbuf_loader.close()

        if(pixbuf is None):
            return
        self.pixbuf = pixbuf

        Gdk.threads_enter()
        self.image_widget.queue_draw()
        Gdk.threads_leave()


if __name__ == '__main__':
    Gdk.threads_init()
    app = KaedeApplication()

    app.run()
