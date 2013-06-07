# -*- coding: utf-8 -*-
'''
Oboinus, a X11 background previewer and setter
Copyright 2011 Suniobo <suniobo@fastmail.fm>

This file is part of Oboinus.

Oboinus is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Oboinus is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Oboinus; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''
import sys
import os
import os.path
import random
import gettext
import traceback
import locale
from subprocess import call
from ConfigParser import ConfigParser, NoSectionError
from . import __version__, __author__, __license__, __email__, __website__

def quit(msg, emergency=True):
    '''Simple wrapper for exit function with message.'''
    sys.stderr.write(msg + '\n')
    sys.exit(1)

try:
    import Image
except ImportError, (strerror):
    quit('Module %s is requred by Oboinus' % strerror)

try:
    import gtk
except ImportError, (strerror):
    quit('Module %s is requred by Oboinus' % strerror)

# Test pygtk version
if gtk.pygtk_version < (2, 6, 0):
    quit('Oboinus requires PyGTK 2.6.0 or newer.')

# i18n 
APP = 'oboinus'
LOCALE_DIR = 'locale'
gettext.install(APP, LOCALE_DIR, unicode=True)

PAGGING = 5
SPACING = 10
CUR_BG_SETTER = 'feh'

if os.getenv("XDG_CONFIG_HOME"):
    CONFIG_DIR = os.getenv("XDG_CONFIG_HOME")
elif os.getenv("HOME"):
    CONFIG_DIR = os.getenv("HOME") + "/.config"
else:
    quit("XDG_CONFIG_HOME or HOME environment variable couldn't be found.")

CONFIG_DIR = CONFIG_DIR + "/oboinus/"

CONFIG_FILE = 'oboinusrc'
BG_FILE     = 'bg_image'

MAIN_PREVIEW_HIGHT = 250
MAIN_PREVIEW_WIDTH = 250
PREVIEW_HIGHT = 135
PREVIEW_WIDTH = 135
USAGE = '''
Usage: oboinus [ OPTIONS ]

X11 background previewer and setter

Options:
    --restore (-r)
        Restores previously saved pictures to the root displays.

    --help (-h) Shows this help.

See also man 1 oboinus'''

class OboinusColor(gtk.gdk.Color):
    '''Wrapper for color.'''

    def parse(self, color_str):
        c = gtk.gdk.color_parse(color_str)
        self.__init__(c.red, c.green, c.blue, c.pixel)

    def to_rgb(self):
        r = int(float(self.red  ) * 255 / 65535)
        g = int(float(self.green) * 255 / 65535)
        b = int(float(self.blue ) * 255 / 65535)
        return (r, g, b)

    def to_string(self):
        color_string = '#%.2X%.2X%.2X' % (self.red/256, self.green/256, self.blue/256)
        return color_string

class OboinusConfig():
    '''Config management.'''

    config_dir = ''
    config_file = ''
    section = 'background'

    def __init__(self):
        self.config_dir  = CONFIG_DIR
        self.config_filename = CONFIG_FILE
        self.config = ConfigParser()

    def load(self):
        config_path = self.get_config_path(create_dir=True)
        if not self.config.read(config_path):
            raise Exception("Can't find config file '%s'" % config_path)

        if not self.config.has_section(self.section):
            raise NoSectionError()
        try:
            filename = self.config.get(self.section, 'filename')
        except:
            filename = ''

        if not os.path.exists(filename):
            raise Exception("Can't read image file '%s'" % filename)
        
    def get(self, key):
        if (key == 'random_image'):
            return self.config.getboolean(self.section, key)
        else:
            return self.config.get(self.section, key)

    def set(self, key, value):
        if not self.config.has_section(self.section):
            self.config.add_section(self.section)

        self.config.set(self.section, key, value)

    def save(self):
        output_file = open(self.get_config_path(True), 'wb')
        self.config.write(output_file)
        output_file.close()

    def get_config_path(self, create_dir=False):
        if (create_dir and os.path.isdir(self.config_dir) != True):
            os.makedirs(self.config_dir)
        return (self.config_dir + self.config_filename)

class BackgroundSetter:
    '''Base class for background setters'''

    filename = ''
    mode     = ''
    bg_color = OboinusColor(red=0, green=0, blue=0, pixel=0)

    def get_bg_filename(self):
        return CONFIG_DIR + BG_FILE

    def _resize_image(self, filename, mode):
        resize_filter = Image.BILINEAR
        screen_width  = gtk.gdk.screen_width()
        screen_height = gtk.gdk.screen_height()
        screen_box = (0, 0, screen_width, screen_height)
        try:
            pic = Image.open(filename)
        except IOError:
            print 'Cannot open file: ', filename
            return
        pic_width, pic_height = pic.size
        format = pic.format
        if mode == 'auto':
            if pic_width < screen_width and pic_height < screen_height:
                mode = 'center'
            elif pic_width > pic_height * 1.5:
                mode = 'vscaled'
            else:
                mode = 'hscaled'

        if mode == 'vscaled':
            pic_width  = pic_width * screen_height / pic_height;
            pic_height = screen_height
            pic = pic.resize((pic_width, pic_height), resize_filter)

            if pic_width > screen_width:
                pic = pic.crop(screen_box)
        elif mode == 'hscaled':
            pic_height = screen_width * pic_height / pic_width;
            pic_width  = screen_width
            pic = pic.resize((pic_width, pic_height), resize_filter)
            if pic_height > screen_height:
                pic = pic.crop(screen_box)
        return (pic, format)

    def set_background(self, filename=None):
        format = 'PNG'
        screen_width  = gtk.gdk.screen_width()
        screen_height = gtk.gdk.screen_height()
        screen_box = (0, 0, screen_width, screen_height)
        im = Image.new('RGB', (screen_width, screen_height))
        im.paste(self.bg_color.to_rgb(), (0, 0, screen_width, screen_height))

        if not filename:
            filename =  self.filename

        if filename:
            pic, format = self._resize_image(filename, self.mode)
            pic_width, pic_height = pic.size
            left  = (screen_width - pic_width) / 2
            upper = (screen_height - pic_height) / 2
            right = left + pic_width
            lower = upper + pic_height
            box = (left, upper, right, lower)
            im.paste(pic, box)
        im.save(self.get_bg_filename(), format)
        self.restore_background()

    def restore_background(self):
        raise Exception('BackgroundSetter::restore_background() is not implemented')

class FehBackgroundSetter(BackgroundSetter):
    ''' Feh setter'''

    def __init__(self):
        self.program = 'feh'

    def restore_background(self):
        return call([self.program, '--bg-center', self.get_bg_filename()])

def get_background_setter():
    '''Factory for BG setter'''
    return FehBackgroundSetter()


class App:
    '''Main app class'''

    filename = ''
    mode = 'scaled'
    random_image = False
    bg_color = OboinusColor(red=0, green=0, blue=0, pixel=0)

    def __init__(self):
        self.config = OboinusConfig()
        try:
            self.config.load()
        except Exception, e:
            print "Warning: ", e.message
        except:
            print "Warning: Can't load config file"
        else:
            self.filename = self.config.get('filename')
            self.mode = self.config.get('mode')
            self.random_image = self.config.get('random_image')
            self.bg_color = OboinusColor()
            self.bg_color.parse(self.config.get('bg_color'))

    def _init_gui(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect('key_press_event', self.on_key_press)
        self.window.connect('destroy',gtk.main_quit)
        self.window.set_border_width(3)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_resizable(False)
        self.window.set_title(_('Oboinus'))

        main_box = gtk.VBox(False, SPACING)
        self.window.add(main_box)
        self._init_menu(main_box)
        self._init_preview(main_box)
        self._init_buttons(main_box)
        self.window.show_all()

    def _init_preview(self, main_box):
        self.image = gtk.Image()

        if not self.filename:
            label_str = 'Please, select file'
        else:
            scaled_buf = gtk.gdk.pixbuf_new_from_file_at_size(self.filename,
                    MAIN_PREVIEW_WIDTH, MAIN_PREVIEW_HIGHT)
            self.image.set_from_pixbuf(scaled_buf)

        if self.filename:
            im = Image.open(self.filename)
            size_str = str(im.size[0]) + 'x' + str(im.size[1]) + ' px'

        main_box.pack_start(self.image, False, False, 10)

        self.color_button = gtk.ColorButton()
        self.color_button.connect('color-set', self.set_backgroundcolor)
        self.color_button.set_color(self.bg_color)

        label = gtk.Label(_('Background color'))
        label.set_line_wrap(True)
        label.set_use_underline(True)

        button_box = gtk.HBox(False, SPACING)
        main_box.pack_start(button_box, False)
        button_box.pack_start(label, False, False)
        button_box.pack_start(self.color_button)

    def _init_buttons(self, main_box):
        button_box = gtk.HBox(False, SPACING)
        main_box.pack_start(button_box, False)
        applyButton = gtk.Button(_('_Apply'), gtk.STOCK_APPLY)
        applyButton.connect('clicked', self.set_background)


        fileselButton = gtk.Button(_('_Browse'), gtk.STOCK_OPEN)
        fileselButton.connect('clicked', self.open_file_dialog)

        self.combobox = gtk.ComboBox()
        liststore = gtk.ListStore(str)
        cell = gtk.CellRendererText()
        self.combobox.pack_start(cell)
        self.combobox.add_attribute(cell, 'text', 0)

        button_box.pack_start(fileselButton, False)
        button_box.pack_start(self.combobox, False)
        button_box.pack_start(applyButton, False)

        liststore.append([_('Auto')])
        liststore.append([_('Vertical scaled')])
        liststore.append([_('Horizontal scaled')])
        liststore.append([_('Center')])
        liststore.append([_('Solid Color')])

        self.combobox.set_model(liststore)
        self.combobox.connect('changed', self.changed_cb)

        if self.mode == 'auto':
            self.combobox.set_active(0)
        elif self.mode == 'vscaled':
            self.combobox.set_active(1)
        elif self.mode == 'hscaled':
            self.combobox.set_active(2)
        elif self.mode == 'center':
            self.combobox.set_active(3)
        else:
            self.combobox.set_active(4)

    def _init_menu(self, main_box):
        ui_menu = '''
        <ui><menubar name="MenuBar">
            <menu action="File">
                <menuitem action="Open"/>
                <menuitem action="Quit"/>
            </menu>
            <menu action="Preferences">
                <menuitem action="Random"/>
            </menu>
            <menu action="Help">
                <menuitem action="About"/>
            </menu>
            </menubar></ui>
         '''
        self._uimanager = gtk.UIManager()
        actiongroup = gtk.ActionGroup('UIManager')
        actiongroup.add_actions([
            ('File', None, _('_File')),
            ('Help', None, _('_Help')),
            ('Preferences', None, _('_Preferences')),
            ('Open', gtk.STOCK_OPEN, _('_Open'), None, _('Open file'), self.open_file_dialog),
            ('Quit', gtk.STOCK_QUIT, _('_Quit'), None, _('Quit Oboinus'), self.exit),
            ('About', gtk.STOCK_ABOUT, _('_About'), None, _('About Oboinus'), self.open_about_dialog),
            ])
        actiongroup.add_toggle_actions([
        ('Random', None, _('_Restore random image'), None, None, self.toggle_random, 
            self.random_image),
        ])
        self._uimanager.insert_action_group(actiongroup, 0)
        self._uimanager.add_ui_from_string(ui_menu)
        menubar = self._uimanager.get_widget('/MenuBar')
        menubar.show()
        main_box.pack_start(menubar, False)

    def toggle_random(self, widget):
        self.random_image = widget.get_active()

    def open_about_dialog(self, widget):
        about_dialog = gtk.AboutDialog()
        about_dialog.set_version(__version__)
        about_dialog.set_name(_('Oboinus'))
        about_dialog.set_authors([
            _('Developer: ') + __author__ + ' <' + __email__ + '>',
            _('Package maintainer: ') + 'Jari Aalto <jari.aalto@cante.net>'
            ])
        about_dialog.set_license(__license__)
        about_dialog.set_website(__website__)
        about_dialog.set_copyright('Copyright 2007 Suniobo <suniobo@fastmail.fm>')
        response = about_dialog.run()
        about_dialog.destroy()

    def open_file_dialog(self, widget):
        self.chooser = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN, \
                buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))

        if self.filename:
            self.chooser.set_current_folder(os.path.dirname(self.filename))
            self.chooser.filename = self.filename
        else:
            self.chooser.set_current_folder(os.environ['HOME'])

        self.chooser.set_default_response(gtk.RESPONSE_OK)

        filter = gtk.FileFilter()
        filter.set_name(_('Images'))
        filter.add_mime_type('image/png')
        filter.add_mime_type('image/jpeg')
        filter.add_mime_type('image/gif')
        filter.add_pattern('*.png')
        filter.add_pattern('*.jpg')
        filter.add_pattern('*.gif')

        self.chooser.add_filter(filter)

        # preview of selected file
        previewImage = gtk.Image()
        self.chooser.set_preview_widget(previewImage)
        self.chooser.set_use_preview_label(False)
        self.chooser.set_transient_for(self.window)
        self.chooser.connect('update-preview', self.update_preview, previewImage)

        response = self.chooser.run()

        if response == gtk.RESPONSE_OK:
            self.filename = self.chooser.get_filename()
            scaled_buf = gtk.gdk.pixbuf_new_from_file_at_size(self.filename, MAIN_PREVIEW_WIDTH, MAIN_PREVIEW_HIGHT)
            self.image.set_from_pixbuf(scaled_buf)
            self.combobox.set_active(0)
        self.chooser.destroy()

    def set_backgroundcolor(self, color_button):
        c = color_button.get_color()
        self.bg_color = OboinusColor(c.red, c.green, c.blue, c.pixel)

    def set_background(self, widget=None):
        background_setter = get_background_setter()
        background_setter.mode = self.mode
        background_setter.bg_color = self.bg_color
        background_setter.filename = self.filename
        background_setter.set_background()

        self.config.set('filename', self.filename)
        self.config.set('mode', self.mode)
        self.config.set('bg_color', self.bg_color.to_string())
        self.config.set('random_image', self.random_image)
        try:
            self.config.save()
        except:
            print "Can't save config file"
            return

    def changed_cb(self, combobox):
        model = combobox.get_model()
        index = combobox.get_active()

        if index == 0:
            self.mode = 'auto'
        elif index == 1:
            self.mode = 'vscaled'
        elif index == 2:
            self.mode = 'hscaled'
        elif index == 3:
            self.mode = 'center'
        else:
            self.mode = 'solid'
            self.filename = ''
        return

    def update_preview(self, file_chooser, preview):
        filename = file_chooser.get_preview_filename()
        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, PREVIEW_WIDTH, PREVIEW_HIGHT)
            preview.set_from_pixbuf(pixbuf)
            have_preview = True
        except:
            have_preview = False
        file_chooser.set_preview_widget_active(have_preview)
        return

    # Shortcuts
    def on_key_press(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        # Exit app by Ctrl-q
        if keyname == 'Escape' or (keyname == 'q' and (event.state & gtk.gdk.CONTROL_MASK)):
            self.exit()

    def exit(self, data=None):
        gtk.main_quit()

    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def restore(self):
        if not self.filename:
            return 1
        background_setter = get_background_setter()
        background_setter.mode = self.mode
        background_setter.bg_color = self.bg_color
        background_setter.filename = self.filename

        if self.random_image:
            file_dir = os.path.dirname(self.filename)
            filename = os.path.join(file_dir,random.choice(os.listdir(file_dir)))
            background_setter.filename = filename
            background_setter.set_background()
        else:
            background_setter.restore_background()
        return 0

    def usage(self):
        print USAGE
        return 0

    def main(self):
        self._init_gui()
        gtk.main()
        return 0
