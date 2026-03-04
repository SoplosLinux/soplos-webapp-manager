import gi
import os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gio

from core.browser_manager import BrowserManager
from core.webapp_manager import WebAppManager
from ui.dialogs.add_webapp_dialog import AddWebAppDialog

class WebAppRow(Gtk.ListBoxRow):
    def __init__(self, webapp, on_delete_callback):
        super().__init__()
        self.webapp = webapp
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        # Icon
        image = Gtk.Image()
        if os.path.exists(webapp.icon_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(webapp.icon_path, 48, 48, True)
                image.set_from_pixbuf(pixbuf)
            except:
                image.set_from_icon_name("applications-internet", Gtk.IconSize.DIALOG)
        else:
            image.set_from_icon_name("applications-internet", Gtk.IconSize.DIALOG)
            
        box.pack_start(image, False, False, 0)
        
        # Text
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        label_name = Gtk.Label(label=f"<b>{webapp.name}</b>")
        label_name.set_use_markup(True)
        label_name.set_halign(Gtk.Align.START)
        
        label_url = Gtk.Label(label=webapp.url)
        label_url.set_halign(Gtk.Align.START)
        
        label_browser = Gtk.Label(label=webapp.browser_id)
        label_browser.set_halign(Gtk.Align.START)
        # Use dim label for browser
        context = label_browser.get_style_context()
        context.add_class('dim-label')
        
        vbox.pack_start(label_name, False, False, 0)
        vbox.pack_start(label_url, False, False, 0)
        vbox.pack_start(label_browser, False, False, 0)
        
        box.pack_start(vbox, True, True, 0)
        
        # Run button
        btn_run = Gtk.Button()
        btn_run.set_image(Gtk.Image.new_from_icon_name("media-playback-start", Gtk.IconSize.BUTTON))
        btn_run.connect("clicked", self.on_run_clicked)
        btn_run.set_valign(Gtk.Align.CENTER)
        box.pack_start(btn_run, False, False, 0)
        
        # Delete button
        btn_delete = Gtk.Button()
        btn_delete.set_image(Gtk.Image.new_from_icon_name("user-trash", Gtk.IconSize.BUTTON))
        btn_delete.get_style_context().add_class('destructive-action')
        btn_delete.set_valign(Gtk.Align.CENTER)
        btn_delete.connect("clicked", lambda w: on_delete_callback(self.webapp))
        box.pack_start(btn_delete, False, False, 10)
        
        self.add(box)
        
    def on_run_clicked(self, widget):
        os.system(f"gtk-launch {os.path.basename(self.webapp.desktop_file)}")

class MainWindow(Gtk.Window):
    def __init__(self, browser_manager: BrowserManager, webapp_manager: WebAppManager, _translate):
        super().__init__(title=_translate("Soplos WebApp Manager"))
        self.browser_manager = browser_manager
        self.webapp_manager = webapp_manager
        self._ = _translate
        
        self.set_default_size(600, 450)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        self.setup_headerbar()
        self.setup_ui()
        self.setup_shortcuts()
        self.load_webapps()
        
    def setup_shortcuts(self):
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        
        key, mod = Gtk.accelerator_parse("<Primary>q")
        accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *args: Gtk.main_quit())
        
    def setup_headerbar(self):
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.set_title(self.get_title())
        self.set_titlebar(self.header)
        
        # Add button
        self.btn_add = Gtk.Button()
        self.btn_add.set_image(Gtk.Image.new_from_icon_name("list-add", Gtk.IconSize.BUTTON))
        self.btn_add.set_tooltip_text(self._("Add WebApp"))
        self.btn_add.connect("clicked", self.on_add_clicked)
        self.header.pack_start(self.btn_add)
        
        # Remove button
        self.btn_remove = Gtk.Button()
        self.btn_remove.set_image(Gtk.Image.new_from_icon_name("list-remove", Gtk.IconSize.BUTTON))
        self.btn_remove.set_tooltip_text(self._("Remove WebApp"))
        self.btn_remove.connect("clicked", self.on_remove_clicked)
        self.btn_remove.set_sensitive(False)
        self.header.pack_start(self.btn_remove)

    def setup_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)
        
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        vbox.pack_start(self.stack, True, True, 0)
        
        # Empty state
        empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        empty_box.set_valign(Gtk.Align.CENTER)
        empty_box.set_halign(Gtk.Align.CENTER)
        
        icon = Gtk.Image.new_from_icon_name("applications-internet", Gtk.IconSize.DIALOG)
        icon.set_pixel_size(128)
        context = icon.get_style_context()
        context.add_class('dim-label')
        empty_box.pack_start(icon, False, False, 0)
        
        label = Gtk.Label(label=self._("No WebApps installed.\nClick the '+' button to add one."))
        label.set_justify(Gtk.Justification.CENTER)
        context = label.get_style_context()
        context.add_class('dim-label')
        empty_box.pack_start(label, False, False, 0)
        
        self.stack.add_named(empty_box, "empty")
        
        # List state
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-selected", self.on_row_selected)
        scrolled.add(self.listbox)
        
        self.stack.add_named(scrolled, "list")
        
    def load_webapps(self):
        # Clear current list
        for child in self.listbox.get_children():
            self.listbox.remove(child)
            
        webapps = self.webapp_manager.list_webapps()
        
        # Force widgets to report as visible before we try to switch stack state
        self.listbox.show_all()
        self.stack.show_all()
        
        if not webapps:
            # Show empty state if no webapps
            self.stack.set_visible_child_name("empty")
        else:
            # Show list
            for wa in webapps:
                row = WebAppRow(wa, self.confirm_and_delete_webapp)
                self.listbox.add(row)
            self.listbox.show_all()
            self.stack.set_visible_child_name("list")
            
        self.btn_remove.set_sensitive(False)
        
    def on_row_selected(self, listbox, row):
        self.btn_remove.set_sensitive(row is not None)
            
    def on_add_clicked(self, widget):
        dialog = AddWebAppDialog(self, self.browser_manager, self._)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            data = dialog.get_data()
            if data['name'] and data['url'] and data['browser']:
                self.webapp_manager.create_webapp(
                    data['name'], 
                    data['url'], 
                    data['icon'], 
                    data['category'], 
                    data['browser'],
                    data['show_navbar']
                )
                self.load_webapps()
        dialog.destroy()
        
    def confirm_and_delete_webapp(self, wa):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=self._("Are you sure you want to delete {}?").format(wa.name)
        )
        dialog.format_secondary_text(self._("This will remove its .desktop file and the isolated browser profile."))
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.webapp_manager.delete_webapp(wa.id_name)
            self.load_webapps()

    def on_remove_clicked(self, widget):
        row = self.listbox.get_selected_row()
        if row:
            self.confirm_and_delete_webapp(row.webapp)
