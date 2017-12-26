#!/usr/bin/python3
import gi
gi.require_version('Gtk', '3.0')
import requests
import config
from gi.repository import Gtk, Gdk, GdkPixbuf
from threading import Thread, Event as threadingEvent


class ImageWidget(Gtk.EventBox):
    ''' Widget for thumbnails '''

    def __init__(self, pixbuf, item_data):
        super(ImageWidget, self).__init__()

        if(pixbuf is None):
            return None

        self.pixbuf = pixbuf
        self.image = Gtk.Image.new_from_pixbuf(self.pixbuf)
        self.image.show()

        self.add(self.image)
        self.connect("button_press_event", self.image_on_click, item_data)

    def image_on_click(self, widget, event_button, data):
        popup_window = ImageWindow(self.pixbuf, data)
        popup_window.show_all()


class SearchThread(Thread):
    ''' Image search worker '''

    def __init__(self, results_container):
        super(SearchThread, self).__init__()
        self.results_container = results_container
        self._stop_event = threadingEvent()

    def search(self, tags):
        self.clear_layout()
        ratings = []
        for rating in ['safe', 'questionable', 'explicit']:
            if config.get_config(
                'Search settings', 'Rating ' + rating, "Enable"
            ) != "Enable":
                ratings.append("-rating:" + rating)

        self.tags = tags + ratings

    def run(self):
        self.add_results(self.results_container, self.tags)

    def add_results(self, container, tags):
        data = search(tags)

        width, height = container.get_size()

        y = 0
        x = 0

        for item in data:
            image_data = get_thumbnail(item)
            if(self.stopped()):
                return

            pixbuf_loader = GdkPixbuf.PixbufLoader.new()
            pixbuf_loader.write(image_data)

            image_pixbuf = pixbuf_loader.get_pixbuf()
            pixbuf_loader.close()
            if(image_pixbuf is None):
                continue

            image_event_widget = ImageWidget(image_pixbuf, item)
            image_event_widget.show()

            if(y + image_pixbuf.get_height() > height):
                y = 0
                x += 160

            Gdk.threads_enter()
            if(x + 160 > width):
                width += 160
                container.set_size(width, height)

            container.put(image_event_widget, x, y)
            Gdk.threads_leave()

            y += image_pixbuf.get_height()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def clear_layout(self):
        self.results_container.do_forall(self.results_container, False,
                                         self.remove_callback, None)
        self.results_container.set_size(
            self.results_container.get_allocated_width(),
            self.results_container.get_allocated_height())

    def remove_callback(self, widget, data):
        widget.destroy()


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super(MainWindow, self).__init__(application=app)
        self.set_title("Kaede")

        self.builder = Gtk.Builder()
        self.builder.add_from_file("main_window_layout.glade")
        self.builder.add_from_file("headerbar_menu.glade")
        self.builder.add_from_file("headerbar_layout.glade")

        content = self.builder.get_object('window-content')
        headerbar = self.builder.get_object('main-headerbar')
        self.add(content)
        self.set_titlebar(headerbar)

        self.thumbnail_container = self.builder.get_object("window-layout")

        self.search_input = self.builder.get_object("tag-search-entry")

        self.search_input.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, "system-search-symbolic")

        self.search_input.connect("activate", self.do_search)
        self.search_tags = None
        self.search_thread = SearchThread(self.thumbnail_container)

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

    def rating_config(self, button, active):
        rating = Gtk.Buildable.get_name(button).split('-')[2]
        if button.get_active():
            config.set_config('Search settings', 'Rating ' + rating, "Enable")
        else:
            config.set_config('Search settings', 'Rating ' + rating, "Disable")
        self.do_search(None)

    def do_search(self, widget):
        if(self.search_thread.ident is not None):
            if(self.search_thread.is_alive()):
                self.search_thread.stop()
                self.search_thread.join(0.5)

            self.search_thread = SearchThread(self.thumbnail_container)
        if widget is not None:
            self.search_tags = widget.get_text()

        if(self.search_tags):
            self.set_title("Kaede - " + self.search_tags)

        self.search_thread.search(self.search_tags.split(' '))
        self.search_thread.start()


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

    def __init__(self, pixbuf=None, data=None):
        super(ImageWindow, self).__init__()

        self.pixbuf = pixbuf
        self.data = data
        self.set_default_size(data["width"], data["height"])

        self.image_widget = Gtk.DrawingArea()
        self.image_widget.connect("draw", self.image_widget_draw, self.pixbuf)
        self.image_widget.set_hexpand(True)
        self.image_widget.set_vexpand(True)

        self.image_widget_container = Gtk.Grid()
        self.image_widget_container.attach(self.image_widget, 0, 0, 1, 1)
        self.connect("button_press_event", self.image_widget_click, self.data)

        self.add(self.image_widget_container)

        if(data):
            self.set_title(data['tags'])
        else:
            self.set_title("Image")

        Thread(target=self.load_image).start()

    def image_widget_draw(self, widget, cairo_context, pixbuf):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

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

    def image_widget_click(self, widget, event_button, data):
        self.pixbuf.savev(data["image"] + ".png", "png", "", "")

    def load_image(self):
        image_data = get_image(self.data)

        pixbuf_loader = GdkPixbuf.PixbufLoader.new()
        pixbuf_loader.write(image_data)

        pixbuf = pixbuf_loader.get_pixbuf()
        pixbuf_loader.close()

        if(pixbuf is None):
            return
        self.pixbuf = pixbuf

        Gdk.threads_enter()
        self.image_widget.connect("draw", self.image_widget_draw, self.pixbuf)
        self.image_widget.queue_draw()
        Gdk.threads_leave()


def _url(key, data=None):
    tail = {'list': "&s=post",
            'comments': "&s=comment"}
    return "http://tbib.org/index.php?page=dapi&json=1" + \
           "&q=index" + tail[key] + "&" + str(data)


def _image_url(post_data):
    return "http://tbib.org//images/" + \
           post_data['directory'] + '/' + post_data['image']


def _thumbnail_url(post_data):
    return "http://tbib.org/thumbnails/" + \
           post_data['directory'] + '/thumbnail_' + post_data['image']


def get_posts():
    return requests.get(_url('list')).json()


def get_image(post_data):
    return requests.get(_image_url(post_data)).content


def get_thumbnail(post_data):
    return requests.get(_thumbnail_url(post_data)).content


def search(tags):
    tag_string = "tags=" + '+'.join(tags)
    response = requests.get(_url('list', tag_string))
    result = []

    if(response.content):
        result = response.json()

    return result


if __name__ == '__main__':
    Gdk.threads_init()
    app = KaedeApplication()

    app.run()
