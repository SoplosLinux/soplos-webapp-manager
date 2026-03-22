import gi
import os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, Gio
from pathlib import Path

from core.browser_manager import BrowserManager, Browser
from core.webapp_manager import WebAppManager, WebApp
from config.constants import APP_ID, APP_NAME, APP_VERSION

from ui.dialogs.add_webapp_dialog import AddWebAppDialog


class WebAppRow(Gtk.ListBoxRow):
    def __init__(self, webapp, on_edit_callback, on_delete_callback, _translate):
        super().__init__()
        self.webapp = webapp
        self._ = _translate
        
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
        context = label_browser.get_style_context()
        context.add_class('dim-label')
        
        vbox.pack_start(label_name, False, False, 0)
        vbox.pack_start(label_url, False, False, 0)
        vbox.pack_start(label_browser, False, False, 0)
        
        box.pack_start(vbox, True, True, 0)
        
        # Run button
        btn_run = Gtk.Button()
        btn_run.set_image(Gtk.Image.new_from_icon_name("media-playback-start", Gtk.IconSize.BUTTON))
        btn_run.set_tooltip_text(self._("Run WebApp"))
        btn_run.connect("clicked", self.on_run_clicked)
        btn_run.set_valign(Gtk.Align.CENTER)
        box.pack_start(btn_run, False, False, 0)
        
        # Edit button
        btn_edit = Gtk.Button()
        btn_edit.set_image(Gtk.Image.new_from_icon_name("document-edit", Gtk.IconSize.BUTTON))
        btn_edit.set_tooltip_text(self._("Edit WebApp"))
        btn_edit.set_valign(Gtk.Align.CENTER)
        btn_edit.connect("clicked", lambda w: on_edit_callback(self.webapp))
        box.pack_start(btn_edit, False, False, 0)
        
        # Delete button
        btn_delete = Gtk.Button()
        btn_delete.set_image(Gtk.Image.new_from_icon_name("user-trash", Gtk.IconSize.BUTTON))
        btn_delete.set_tooltip_text(self._("Delete WebApp"))
        btn_delete.get_style_context().add_class('destructive-action')
        btn_delete.set_valign(Gtk.Align.CENTER)
        btn_delete.connect("clicked", lambda w: on_delete_callback(self.webapp))
        box.pack_start(btn_delete, False, False, 10)
        
        self.add(box)
        
    def on_run_clicked(self, widget):
        os.system(f"gtk-launch {os.path.basename(self.webapp.desktop_file)}")


class MainWindow(Gtk.ApplicationWindow):
    """Main Application Window."""
    def __init__(self, app, browser_manager: BrowserManager, webapp_manager: WebAppManager, environment_detector, _translate, assets_dir):
        super().__init__(application=app, title=_translate(APP_NAME))
        self.browser_manager = browser_manager
        self.webapp_manager = webapp_manager
        self.environment_detector = environment_detector
        self._ = _translate
        self.assets_dir = Path(assets_dir) if assets_dir else None
        
        self.set_default_size(600, 450)
        self.set_position(Gtk.WindowPosition.CENTER)

        _css = Gtk.CssProvider()
        _css.load_from_data(b"""
            window { background-color: #2b2b2b; color: #ffffff; }
            list { background-color: #2b2b2b; color: #ffffff; }
            list row { background-color: #2b2b2b; color: #ffffff; border-bottom: 1px solid #3c3c3c; }
            list row:hover { background-color: #333333; }
            scrolledwindow, scrolledwindow viewport { background-color: #2b2b2b; }
            label { color: #ffffff; }
            label.dim-label { color: #888888; }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), _css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.setup_headerbar()
        self.setup_ui()
        self.setup_shortcuts()
        self.load_webapps()
        self.connect("key-press-event", self._on_key_press)
        
    def setup_shortcuts(self):
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        
        key, mod = Gtk.accelerator_parse("<Primary>q")
        accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *args: self.get_application().quit())
        
    def setup_headerbar(self):
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.set_title(self.get_title())
        self.header.set_decoration_layout("menu:minimize,maximize,close")
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
        
        # Web browser compass icon (as in screenshot1.png)
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

        # Status bar at bottom
        self._create_status_bar(vbox)

    def _create_status_bar(self, main_vbox):
        """Create a clean status bar with system info and version."""
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_box.set_margin_start(15)
        status_box.set_margin_end(15)
        status_box.set_margin_top(8)
        status_box.set_margin_bottom(8)
        
        # Left side: System info
        env_info = self.environment_detector.detect_all()
        desktop_name = self._translate_desktop_name(env_info['desktop_environment'])
        protocol_name = self._translate_protocol_name(env_info['display_protocol'])
        
        status_text = self._("Ready - {desktop} on {protocol}").format(
            desktop=desktop_name,
            protocol=protocol_name
        )
        
        self.status_label = Gtk.Label(label=status_text)
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.get_style_context().add_class('status-label')
        status_box.pack_start(self.status_label, False, False, 0)
        
        # Right side: Version info
        version_text = f"v{APP_VERSION}"
        version_label = Gtk.Label(label=version_text)
        version_label.set_halign(Gtk.Align.END)
        version_label.get_style_context().add_class('dim-label')
        status_box.pack_end(version_label, False, False, 0)
        
        main_vbox.pack_end(status_box, False, False, 0)

    def _translate_desktop_name(self, desktop_env):
        """Translate desktop environment name."""
        desktop_map = {
            'gnome': self._("GNOME"),
            'kde': self._("KDE Plasma"),
            'plasma': self._("KDE Plasma"),
            'xfce': self._("XFCE"),
            'unknown': self._("Unknown")
        }
        return desktop_map.get(desktop_env.lower(), self._("Unknown"))

    def _translate_protocol_name(self, protocol):
        """Translate display protocol name."""
        protocol_map = {
            'x11': self._("X11"),
            'wayland': self._("Wayland"),
            'unknown': self._("Unknown")
        }
        return protocol_map.get(protocol.lower(), self._("Unknown"))

    def load_webapps(self):
        for child in self.listbox.get_children():
            self.listbox.remove(child)
            
        webapps = self.webapp_manager.list_webapps()
        
        self.listbox.show_all()
        self.stack.show_all()
        
        if not webapps:
            self.stack.set_visible_child_name("empty")
        else:
            for wa in webapps:
                row = WebAppRow(wa, self.edit_webapp, self.confirm_and_delete_webapp, self._)
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
                    data['show_navbar'],
                    data['extra_params']
                )
                self.load_webapps()
        dialog.destroy()
        
    def edit_webapp(self, wa):
        """Open a dialog to edit the webapp properties (name, url, icon, browser, navbar)."""
        dialog = Gtk.Dialog(
            title=self._("Edit WebApp"),
            transient_for=self,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        dialog.set_default_size(450, 450)
        dialog.set_border_width(10)
        
        box = dialog.get_content_area()
        box.set_spacing(15)
        
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        box.pack_start(grid, True, True, 0)
        
        # Name
        entry_name = Gtk.Entry()
        entry_name.set_text(wa.name)
        grid.attach(Gtk.Label(label=self._("Name:")), 0, 0, 1, 1)
        grid.attach(entry_name, 1, 0, 2, 1)
        
        # URL
        entry_url = Gtk.Entry()
        entry_url.set_text(wa.url)
        grid.attach(Gtk.Label(label=self._("Web Address:")), 0, 1, 1, 1)
        grid.attach(entry_url, 1, 1, 2, 1)
        
        # Icon
        icon_image = Gtk.Image()
        selected_icon = [wa.icon_path]
        if os.path.exists(wa.icon_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(wa.icon_path, 48, 48, True)
                icon_image.set_from_pixbuf(pixbuf)
            except:
                icon_image.set_from_icon_name("applications-internet", Gtk.IconSize.DIALOG)
        else:
            icon_image.set_from_icon_name("applications-internet", Gtk.IconSize.DIALOG)
        
        icon_btn = Gtk.Button(label=self._("Select Icon"))
        def on_icon_clicked(button):
            chooser = Gtk.FileChooserDialog(
                title=self._("Select an icon"),
                parent=dialog,
                action=Gtk.FileChooserAction.OPEN,
            )
            chooser.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
            )
            filt = Gtk.FileFilter()
            filt.set_name(self._("Images (PNG, SVG, JPG)"))
            filt.add_mime_type("image/png")
            filt.add_mime_type("image/svg+xml")
            filt.add_mime_type("image/jpeg")
            chooser.add_filter(filt)
            if chooser.run() == Gtk.ResponseType.OK:
                path = chooser.get_filename()
                selected_icon[0] = path
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 48, 48, True)
                    icon_image.set_from_pixbuf(pixbuf)
                except:
                    pass
            chooser.destroy()
        
        icon_btn.connect("clicked", on_icon_clicked)
        grid.attach(Gtk.Label(label=self._("Icon:")), 0, 2, 1, 1)
        grid.attach(icon_image, 1, 2, 1, 1)
        grid.attach(icon_btn, 2, 2, 1, 1)
        
        # Browser
        combo_browser = Gtk.ComboBoxText()
        browsers = self.browser_manager.get_browsers_list()
        active_index = 0
        for i, brw in enumerate(browsers):
            combo_browser.append(brw.id_name, brw.display_name)
            if brw.id_name == wa.browser_id:
                active_index = i
        combo_browser.set_active(active_index)
        grid.attach(Gtk.Label(label=self._("Browser:")), 0, 3, 1, 1)
        grid.attach(combo_browser, 1, 3, 2, 1)
        
        # Navbar Switch
        switch_navbar = Gtk.Switch()
        switch_navbar.set_active(wa.show_navbar)
        switch_navbar.set_halign(Gtk.Align.START)
        grid.attach(Gtk.Label(label=self._("Navigation Bar:")), 0, 4, 1, 1)
        grid.attach(switch_navbar, 1, 4, 2, 1)

        # Incognito Switch
        switch_incognito = Gtk.Switch()
        switch_incognito.set_active(wa.is_incognito)
        switch_incognito.set_halign(Gtk.Align.START)
        grid.attach(Gtk.Label(label=self._("Incognito Mode:")), 0, 5, 1, 1)
        grid.attach(switch_incognito, 1, 5, 2, 1)

        # Extra Parameters
        entry_extra_params = Gtk.Entry()
        entry_extra_params.set_text(wa.extra_params)
        grid.attach(Gtk.Label(label=self._("Extra Parameters:")), 0, 6, 1, 1)
        
        params_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        params_box.pack_start(entry_extra_params, True, True, 0)
        
        btn_help = Gtk.Button()
        btn_help.set_image(Gtk.Image.new_from_icon_name("help-about", Gtk.IconSize.BUTTON))
        btn_help.set_tooltip_text(self._("Common Parameters Help"))
        def on_help_clicked(btn):
            help_text = (
                f"<b>--start-maximized</b>: {self._('Forces the WebApp to occupy the full screen at startup.')}\n\n"
                f"<b>--disable-features=TabHoverCard</b>: {self._('Prevents floating bubbles when hovering over tabs (very useful in WebApp mode).')}\n\n"
                f"<b>--force-dark-mode</b>: {self._('Forces the website to render in dark mode, even if not natively supported.')}\n\n"
                f"<b>--user-agent=\"...\"</b>: {self._('Simulate a different browser or device.')}\n\n"
                f"<b>--proxy-server=\"IP:PORT\"</b>: {self._('Use a specific proxy for this WebApp.')}\n\n"
                f"<b>--window-size=WIDTH,HEIGHT</b>: {self._('Set a fixed window size.')}\n\n"
                f"<b>--disable-notifications</b>: {self._('Disable all website notifications.')}\n\n"
                f"<b>--shm-size=2gb</b>: {self._('Increase shared memory (useful for heavy apps in containers).')}"
            )
            help_dialog = Gtk.MessageDialog(
                transient_for=dialog,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=self._("Browser Parameters Help")
            )
            help_dialog.set_markup(help_text)
            help_dialog.run()
            help_dialog.destroy()
        
        btn_help.connect("clicked", on_help_clicked)
        params_box.pack_start(btn_help, False, False, 0)
        
        grid.attach(params_box, 1, 6, 2, 1)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            new_name = entry_name.get_text().strip()
            new_url = entry_url.get_text().strip()
            new_icon = selected_icon[0]
            new_browser_id = combo_browser.get_active_id()
            new_show_navbar = switch_navbar.get_active()
            new_extra_params = entry_extra_params.get_text().strip()
            new_is_incognito = switch_incognito.get_active()
            
            self.webapp_manager.update_webapp(
                wa.id_name,
                new_name=new_name,
                new_icon=new_icon,
                new_url=new_url,
                new_browser_id=new_browser_id,
                new_show_navbar=new_show_navbar,
                new_extra_params=new_extra_params,
                new_is_incognito=new_is_incognito
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

    def _show_about(self, *args):
        dialog = Gtk.AboutDialog()
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        dialog.set_program_name(APP_NAME)
        dialog.set_version(APP_VERSION)
        dialog.set_comments(self._("Web application manager for Soplos Linux."))
        dialog.set_website("https://soplos.org")
        dialog.set_website_label("soplos.org")
        dialog.set_authors(["Sergi Perich <info@soploslinux.com>"])
        dialog.set_license_type(Gtk.License.GPL_3_0)
        icon_path = Path(__file__).parent.parent / 'assets' / 'icons' / '64x64' / 'org.soplos.webappmanager.png'
        if icon_path.exists():
            dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file_at_scale(str(icon_path), 48, 48, True))
        _about_css = Gtk.CssProvider()
        _about_css.load_from_data(b"""
            dialog, messagedialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            dialog .background, messagedialog .background {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            dialog > box, messagedialog > box {
                background-color: #2b2b2b;
            }
            dialog label, messagedialog label {
                color: #ffffff;
            }
            dialog button, messagedialog button {
                background-image: none;
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px 14px;
                min-height: 0;
                box-shadow: none;
            }
            dialog button:hover, messagedialog button:hover {
                background-color: #444444;
                border-color: #ff8800;
            }
            dialog stackswitcher button {
                border-radius: 100px;
                background-color: #2b2b2b;
                background-image: none;
                border: 1px solid #3c3c3c;
                font-weight: normal;
                padding: 4px 16px;
                min-height: 0;
                box-shadow: none;
                color: #ffffff;
            }
            dialog stackswitcher button:hover {
                background-color: #444444;
                border-color: #ff8800;
            }
            dialog stackswitcher button:checked {
                background-color: #444444;
                color: #ffffff;
            }
            dialog scrolledwindow,
            dialog scrolledwindow viewport {
                background-color: #2b2b2b;
                border-radius: 0;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), _about_css,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        dialog.run()
        dialog.destroy()

    def _on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_F1:
            self._show_about()
            return True
        return False

    def on_remove_clicked(self, widget):
        row = self.listbox.get_selected_row()
        if row:
            self.confirm_and_delete_webapp(row.webapp)
