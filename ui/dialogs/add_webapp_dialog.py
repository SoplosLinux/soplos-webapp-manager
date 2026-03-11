import gi
import os
from gi.repository import Gtk, GdkPixbuf

gi.require_version('Gtk', '3.0')

from utils.favicon import download_favicon

class AddWebAppDialog(Gtk.Dialog):
    def __init__(self, parent, browser_manager, _translate):
        super().__init__(title=_translate("Add WebApp"), transient_for=parent)
        self.browser_manager = browser_manager
        self._ = _translate
        self.selected_icon_path = ""
        
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        self.set_default_size(400, 300)
        self.set_border_width(10)
        
        box = self.get_content_area()
        box.set_spacing(10)
        
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        box.pack_start(grid, True, True, 0)
        
        # Name
        self.entry_name = Gtk.Entry()
        self.entry_name.set_placeholder_text(self._("e.g. YouTube"))
        grid.attach(Gtk.Label(label=self._("Name:")), 0, 0, 1, 1)
        grid.attach(self.entry_name, 1, 0, 2, 1)
        
        # URL
        self.entry_url = Gtk.Entry()
        self.entry_url.set_placeholder_text("https://...")
        self.entry_url.connect("focus-out-event", self.on_url_focus_out)
        grid.attach(Gtk.Label(label=self._("Web Address:")), 0, 1, 1, 1)
        grid.attach(self.entry_url, 1, 1, 2, 1)
        
        # Icon
        self.icon_image = Gtk.Image.new_from_icon_name("applications-internet", Gtk.IconSize.DIALOG)
        self.icon_btn = Gtk.Button(label=self._("Select Icon"))
        self.icon_btn.connect("clicked", self.on_icon_clicked)
        grid.attach(Gtk.Label(label=self._("Icon:")), 0, 2, 1, 1)
        grid.attach(self.icon_image, 1, 2, 1, 1)
        grid.attach(self.icon_btn, 2, 2, 1, 1)
        
        # Category
        self.combo_category = Gtk.ComboBoxText()
        categories = [
            ("Network", self._("Network")),
            ("Game", self._("Game")),
            ("Office", self._("Office")),
            ("AudioVideo", self._("AudioVideo")),
            ("Development", self._("Development")),
            ("Utility", self._("Utility"))
        ]
        for cat_id, cat_name in categories:
            self.combo_category.append(cat_id, cat_name)
        self.combo_category.set_active(0)
        grid.attach(Gtk.Label(label=self._("Category:")), 0, 3, 1, 1)
        grid.attach(self.combo_category, 1, 3, 2, 1)
        
        # Browser
        self.combo_browser = Gtk.ComboBoxText()
        browsers = self.browser_manager.get_browsers_list()
        for i, brw in enumerate(browsers):
            self.combo_browser.append(brw.id_name, brw.display_name)
        if browsers:
            self.combo_browser.set_active(0)
        grid.attach(Gtk.Label(label=self._("Browser:")), 0, 4, 1, 1)
        grid.attach(self.combo_browser, 1, 4, 2, 1)
        
        # Navbar Switch
        self.switch_navbar = Gtk.Switch()
        self.switch_navbar.set_active(False)
        self.switch_navbar.set_halign(Gtk.Align.START)
        grid.attach(Gtk.Label(label=self._("Navigation Bar:")), 0, 5, 1, 1)
        grid.attach(self.switch_navbar, 1, 5, 2, 1)

        # Incognito Switch
        self.switch_incognito = Gtk.Switch()
        self.switch_incognito.set_active(False)
        self.switch_incognito.set_halign(Gtk.Align.START)
        grid.attach(Gtk.Label(label=self._("Incognito Mode:")), 0, 6, 1, 1)
        grid.attach(self.switch_incognito, 1, 6, 2, 1)

        # Extra Parameters
        self.entry_extra_params = Gtk.Entry()
        self.entry_extra_params.set_placeholder_text(self._("e.g. --start-maximized"))
        grid.attach(Gtk.Label(label=self._("Extra Parameters:")), 0, 7, 1, 1)
        
        params_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        params_box.pack_start(self.entry_extra_params, True, True, 0)
        
        btn_help = Gtk.Button()
        btn_help.set_image(Gtk.Image.new_from_icon_name("help-about", Gtk.IconSize.BUTTON))
        btn_help.set_tooltip_text(self._("Common Parameters Help"))
        btn_help.connect("clicked", self.on_help_clicked)
        params_box.pack_start(btn_help, False, False, 0)
        
        grid.attach(params_box, 1, 7, 2, 1)
        
        self.show_all()

    def on_help_clicked(self, widget):
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
        
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=self._("Browser Parameters Help")
        )
        dialog.set_markup(help_text)
        dialog.run()
        dialog.destroy()

    def on_url_focus_out(self, widget, event):
        """Try to auto-download the favicon if the user leaves the URL input and there is no manual icon."""
        url = self.entry_url.get_text().strip()
        if url and not self.selected_icon_path:
            # Assign a temporary directory in ~/.cache
            cache_dir = os.path.expanduser("~/.cache/soplos-webapp-manager/icons")
            try:
                icon_path = download_favicon(url, cache_dir)
                if icon_path and os.path.exists(icon_path):
                    self.set_icon(icon_path)
            except Exception as e:
                print(f"Error fetching favicon: {e}")
        return False

    def on_icon_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title=self._("Select an icon"),
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )

        filter_image = Gtk.FileFilter()
        filter_image.set_name(self._("Images (PNG, SVG, JPG)"))
        filter_image.add_mime_type("image/png")
        filter_image.add_mime_type("image/svg+xml")
        filter_image.add_mime_type("image/jpeg")
        dialog.add_filter(filter_image)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.set_icon(dialog.get_filename())
        dialog.destroy()
        
    def set_icon(self, path):
        self.selected_icon_path = path
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 48, 48, True)
            self.icon_image.set_from_pixbuf(pixbuf)
        except Exception as e:
            print(f"Cannot load icon {path}: {e}")

    def get_data(self):
        return {
            "name": self.entry_name.get_text(),
            "url": self.entry_url.get_text(),
            "icon": self.selected_icon_path or "applications-internet",
            "category": self.combo_category.get_active_id(),
            "browser": self.combo_browser.get_active_id(),
            "show_navbar": self.switch_navbar.get_active(),
            "extra_params": self.entry_extra_params.get_text().strip(),
            "is_incognito": self.switch_incognito.get_active()
        }
