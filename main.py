#!/usr/bin/python3
import os
import gi
from config import KaedeConfig
import threads
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

config = None


class ThumbnailWidget(Gtk.EventBox):
    """Widget for thumbnails."""

    def __init__(self, data):
        """Init function.

        Args:
            data (dict): Image data.
        """
        super(ThumbnailWidget, self).__init__()

        if(data['thumbnail_pixbuf'] is None):
            return None

        self.data = data
        self.image = Gtk.Image.new_from_pixbuf(self.data['thumbnail_pixbuf'])
        self.image.show()

        self.add(self.image)

    def image_on_click(self, widget, event_button, parent_window):
        """Handle clicks on the thumbnail.

        Args:
            widget (Gtk.Widget): Signal receiver.
            event_button (Gtk.EventButton): Button pressed.
            parent_window (Gtk.Window): Window holding the images data.
        """
        popup_window = ImageWindow(self.data, parent_window)
        popup_window.show_all()

    def get_size(self):
        """Return the thumbnail size."""
        return self.data['thumbnail_pixbuf'].get_width(), \
            self.data['thumbnail_pixbuf'].get_height()


class MainWindow(Gtk.ApplicationWindow):
    """Main window class."""

    def __init__(self, app):
        """Init function.

        Args:
            app (Gtk.Application): The application.
        """
        super(MainWindow, self).__init__(application=app)
        global config
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
        self.search_thread = threads.SearchThread(self)

        self.config_fields = \
            {'rating': {
                'safe':
                self.builder.get_object("switch-rating-safe"),

                'questionable':
                self.builder.get_object("switch-rating-questionable"),

                'explicit':
                self.builder.get_object("switch-rating-explicit")
            },
             'downloads': {
                'path': self.builder.get_object("button-download-path")
            }
            }
        for switch_name, switch_object in self.config_fields['rating'].items():
            rating = switch_name
            switch_object.set_active(
                config['search']['rating-' + rating] != "False"
            )
            switch_object.connect("notify::active", self.rating_config)

        self.config_fields['downloads']['path']\
            .set_current_folder(config['download']['folder'])
        self.config_fields['downloads']['path']\
            .connect("file-set", self.set_download_path)

    def set_download_path(self, widget):
        """Handle download folder setting changes.

        Args:
            widget (Gtk.FileChooser): Signal receiver.
        """
        global config
        folder = widget.get_uri().split('file://')[-1]
        config['download']['folder'] = folder

    def wall_scroll(self, widget, scroll_event):
        """Handle scrolling events so it works with the mouse wheel.

        Args:
            widget (Gtk.Widget): Signal receiver.
            scroll_event (Gdk.ScrollEvent): Scroll displacement.
        """
        hadj = widget.get_hadjustment()
        hadj.set_value(hadj.get_value() +
                       scroll_event.delta_y * hadj.get_step_increment())

    def overscroll(self, widget, pos):
        """Handle edge reaching so we can do some sort of infinite scroll.

        Args:
            widget (Gtk.ScrolledWindow): Signal receiver.
            pos (Gtk.PositionType): Edge side reached.
        """
        if pos is Gtk.PositionType.RIGHT and not self.search_thread.is_alive():
            self.do_search(None, True)

    def rating_config(self, button, active):
        """Handle rating preference changes.

        Args:
            button (Gtk.Switch): Signal receiver.
            active (GObject.ParamSpec): New state of the switch.
        """
        global config
        rating = Gtk.Buildable.get_name(button).split('-')[2]
        if button.get_active():
            config['search']['rating-' + rating] = "True"
        else:
            config['search']['rating-' + rating] = "False"
        self.do_search(None)

    def update_on_resize(self, widget, allocation):
        """Handle resizing so we can adjust the wall container limits and size.

        Args:
            widget (Gtk.Window): Signal receiver.
            allocation (Gdk.Rectangle): New size allocation.
        """
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
        """Append the thumbnail to the wall.

         Add the thumbnail only if it wasn't added before
         to prevent repeated results

        Args:
            data (dict): Image/thumbnail information.
        """
        if not [thumb for
                thumb in self.thumbnails['data'] if thumb["id"] == data["id"]]:
            self.thumbnails['data'].append(data)
            self.do_add_thumbnail(data)

    def do_add_thumbnail(self, data):
        """Efectively add the thumbnail to the wall.

        Args:
            data (dict): Image/thumbnail information.
        """
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
        """Remove all elements on the wall and reset it's size."""
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
        """Remove a widget.

        Args:
            widget (Gtk.Widget): Signal receiver.
            data (None): unused.
        """
        widget.destroy()

    def do_search(self, widget, new_page=False):
        """Start searching using the ```activate``` signal.

        Args:
            widget (Gtk.Entry): Entry containing the tags.
            new_page (bool): Whether to change the page.
        """
        if not new_page:
            self.thumbnails['data'][:] = []
            if(self.search_thread.ident is not None):
                if(self.search_thread.is_alive()):
                    self.search_thread.stop()
                    self.search_thread.join(0.5)
            self.clear_layout()

        self.search_thread = threads.SearchThread(self)
        if widget is not None:
            self.search_tags = widget.get_text()
        if(self.search_tags):
            self.set_title("Kaede - " + self.search_tags)
        self.search_thread.search(self.search_tags.split(' '),
                                  self.thumbnails['page'])
        self.search_thread.start()
        self.thumbnails['page'] += 1


class KaedeApplication(Gtk.Application):
    """Application container."""

    def __init__(self):
        """Init function."""
        super(KaedeApplication, self).__init__()
        self.app_window = None

    def do_activate(self):
        """Start working."""
        self.app_window = MainWindow(self)
        self.app_window.show_all()
        self.app_window.do_search(self.app_window.search_input)

    def do_startup(self):
        """Do the startup thing."""
        Gtk.Application.do_startup(self)

    def do_shutdown(self):
        """Clear the app."""
        if(self.app_window.search_thread.is_alive()):
            self.app_window.search_thread.stop()
            self.app_window.search_thread.join(0.5)
        Gtk.Application.do_shutdown(self)


class ImageWindow(Gtk.Window):
    """To show the full-size image."""

    def __init__(self, data, parent_window=None):
        """Init function.

        Args:
            data (dict):  Image/thumbnail information.
            parent_window (Gtk.Window): Window holding all the thumbnails.
        """
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
        self.props_button = self.builder.get_object('button-props')

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
        self.props_button.connect('clicked', self.show_props, self.data)

        if self.parent_window is None:
            self.prev_button.destroy()
            self.next_button.destroy()
        else:
            self.prev_button.connect('clicked', self.prev_image)
            self.next_button.connect('clicked', self.next_image)

        self.loader = threads.ImageLoadThread(owner=self)
        self.loader.start()

    def show_props(self, widget, data):
        """Show a window with the image properties.

        Args:
            widget (Gtk.Button): Button pressed.
            data (dict): Image properties.
        """
        dialog = Gtk.Window(title="Details - " + str(data['id']))
        header = Gtk.HeaderBar(title="Details", subtitle=data['id'],
                               show_close_button=True)
        dialog.set_titlebar(header)
        dialog.set_transient_for(self)
        dialog.set_modal(self)
        dialog.set_default_size(300, 300)

        grid = Gtk.Grid(column_spacing=10, margin=10)
        container = Gtk.ScrolledWindow()
        container.add(grid)
        dialog.add(container)

        labelID = Gtk.Label(label="<b>ID</b>", use_markup=True)
        labelID.set_xalign(1.0)
        valueID = Gtk.Label(label=data['id'])
        valueID.set_xalign(0.0)
        grid.attach(labelID, 0, 0, 1, 1)
        grid.attach_next_to(valueID, labelID,
                            Gtk.PositionType.RIGHT, 1, 1)

        labelAuthor = Gtk.Label(label="<b>Author</b>", use_markup=True)
        labelAuthor.set_xalign(1.0)
        if 'author' not in data:
            data['author'] = "Unknown"
        valueAuthor = Gtk.Label(label=data['author'])
        valueAuthor.set_xalign(0.0)
        grid.attach(labelAuthor, 0, 1, 1, 1)
        grid.attach_next_to(valueAuthor, labelAuthor,
                            Gtk.PositionType.RIGHT, 1, 1)

        labelRating = Gtk.Label(label="<b>Rating</b>", use_markup=True)
        labelRating.set_xalign(1.0)
        valueRating = Gtk.Label(label=data['rating'])
        valueRating.set_xalign(0.0)
        grid.attach(labelRating, 0, 2, 1, 1)
        grid.attach_next_to(valueRating, labelRating,
                            Gtk.PositionType.RIGHT, 1, 1)

        labelTags = Gtk.Label(label="<b>Tags</b>", use_markup=True)
        labelTags.set_xalign(1.0)
        valueTags = Gtk.Label(label=data['tags'], wrap=True)
        valueTags.set_xalign(0.0)
        grid.attach(labelTags, 0, 3, 1, 1)
        grid.attach_next_to(valueTags, labelTags,
                            Gtk.PositionType.RIGHT, 1, 1)

        dialog.show_all()

    def next_image(self, widget):
        """Show and load the next image on the wall.

        Args:
            widget (Gtk.Button): Button pressed.
        """
        data = [thumb
                for thumb in self.parent_window.thumbnails['data']
                if thumb["id"] > self.data["id"]]
        if data:
            self.data = data[-1]
        else:
            return False
        self.pixbuf = self.data['thumbnail_pixbuf']
        self.image_widget.queue_draw()
        self.loader.stop()
        self.loader = threads.ImageLoadThread(owner=self)
        self.loader.start()

    def prev_image(self, widget):
        """Show and load the previous image on the wall.

        Args:
            widget (Gtk.Button): Button pressed.
        """
        data = [thumb
                for thumb in self.parent_window.thumbnails['data']
                if thumb["id"] < self.data["id"]]
        if data:
            self.data = data[0]
        else:
            return False
        self.pixbuf = self.data['thumbnail_pixbuf']
        self.image_widget.queue_draw()
        self.loader.stop()
        self.loader = threads.ImageLoadThread(owner=self)
        self.loader.start()

    def image_widget_draw(self, widget, cairo_context):
        """Draw the image according the current sizes.

        Args:
            widget (Gtk.Widget): Where the draw signal was directed.
            cairo_context (cairo.Context): Cairo context
        """
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
        """Save image to local disk.

        Args:
            widget (Gtk.Widget): Signal receiver.
            data (dict): Image properties.
        """
        global config
        save_dir = config['download']['folder']
        image_save_path = os.path.join(save_dir, data["image"])
        save_thread = threads.SaveImageThread(path=image_save_path,
                                              pixbuf=self.pixbuf)
        save_thread.start()


if __name__ == '__main__':
    Gdk.threads_init()
    app = KaedeApplication()

    config = KaedeConfig()
    try:
        app.run()
    finally:
        config.save()
