import json
import os
import socket
import gi
import psutil
import subprocess
import requests
import time

from gi.repository import Gray, Gtk, GdkPixbuf, GLib, Gio, Playerctl
from fabric.core.fabricator import Fabricator
from fabric import Application
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.image import Image
#if os.environ.get("XDG_SESSION_TYPE") == "x11":
#from fabric.widgets.x11 import X11Window as Window
from cadrx11 import X11Window as Window
#else:
#    from fabric.widgets.wayland import WaylandWindow as Window
 
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.overlay import Overlay
from fabric.widgets.eventbox import EventBox
from fabric.widgets.datetime import DateTime
from fabric.widgets.circularprogressbar import CircularProgressBar
from fabric.system_tray.widgets import SystemTray
from fabric.utils import invoke_repeater, monitor_file, bulk_replace, FormattedString, get_relative_path, DesktopApp, get_desktop_applications
from libqtile.command.client import InteractiveCommandClient
#from modules.osd import OSDContainer


gi.require_version("Gtk", "3.0")
gi.require_version("Gray", "0.1")

from typing import ClassVar
from fabric.audio import Audio
from fabric.widgets.revealer import Revealer
from fabric.widgets.scale import Scale, ScaleMark




c = InteractiveCommandClient()

SOCKET_PATH = "/tmp/fabric_qtile_socket"

AUDIO_WIDGET = True

if AUDIO_WIDGET is True:
    try:
        from fabric.audio.service import Audio
    except Exception as e:
        print(e)
        AUDIO_WIDGET = False



class OSDContainer(Window):
    """Janela simples que aceita um texto e o exibe."""

    def __init__(self, text):
        super().__init__(title="Config Editor", size=(30, 30))

        # Cria um widget Label para exibir o texto
        self.label = Gtk.Label(label="dumbtext")
        
        # Adiciona o label à janela
        self.add(self.label)
        

class SystemTrayWidget(Gtk.Box):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.watcher = Gray.Watcher()
        self.watcher.connect("item-added", self.on_item_added)

    def on_item_added(self, _, identifier: str):
        item = self.watcher.get_item_for_identifier(identifier)
        item_button = self.do_bake_item_button(item)
        item_button.show_all()
        self.add(item_button)

    def do_bake_item_button(self, item) -> Gtk.Button:
        button = Gtk.Button()

        # context menu handler
        button.connect(
            "button-press-event",
            lambda _, event: item.get_menu().popup_at_pointer(event),
        )

        # get pixel map of item's icon
        pixmap = Gray.get_pixmap_for_pixmaps(item.get_icon_pixmaps(), 24)

        # convert the pixmap to a pixbuf
        pixbuf: GdkPixbuf.Pixbuf = (
            pixmap.as_pixbuf(32, GdkPixbuf.InterpType.HYPER)
            if pixmap is not None
            else Gtk.IconTheme().load_icon(
                item.get_icon_name(),
                36,
                Gtk.IconLookupFlags.FORCE_SIZE,
            )
        )

        # resize/scale the pixbuf
        pixbuf.scale_simple(36 * 3, 36 * 3, GdkPixbuf.InterpType.HYPER)

        image = Gtk.Image(pixbuf=pixbuf, pixel_size=36 * 3)
        button.set_image(image)

        return button


class ConfigEditorWindow(Window):
    SCHEMES = [
        "scheme-content", "scheme-expressive", "scheme-fidelity", "scheme-fruit-salad",
        "scheme-monochrome", "scheme-neutral", "scheme-rainbow", "scheme-tonal-spot"
    ]
    
    BG_POSITIONS = [
    "top left", "top center", "top right",
    "center left", "center center", "center right",
    "bottom left", "bottom center", "bottom right"
    ]
    
    THEME_COLORS = ["dark", "light"]

    def __init__(self, config_file):
        super().__init__(title="Config Editor", size=(400, 800))
        self.config_file = config_file
        

        self.load_config()

        self.wallpaper_file_chooser = Gtk.FileChooserButton(title="Select Wallpaper", action=Gtk.FileChooserAction.OPEN)
        self.wallpaper_file_chooser.set_filename(self.config.get("wallpaper", ""))

        

    
        self.location_entry = Entry(text=self.config.get("location", ""), placeholder_text="Location")

    
        self.scheme_buttons = []
        scheme_box = Box(orientation='horizontal', spacing=5)
        for scheme in self.SCHEMES:
            button = Button(label=scheme, on_clicked=self.on_scheme_clicked)
            scheme_box.add(button)
            self.scheme_buttons.append(button)

    
        self.theme_buttons = []
        theme_box = Box(orientation='horizontal', spacing=5)
        for theme in self.THEME_COLORS:
            button = Button(label=theme, on_clicked=self.on_theme_clicked)
            theme_box.add(button)
            self.theme_buttons.append(button)

    
        self.background_position_buttons = []
        background_position_box = Box(orientation='horizontal', spacing=5)
        for position in self.BG_POSITIONS:
            button = Button(label=position, on_clicked=self.on_background_position_clicked)
            background_position_box.add(button)
            self.background_position_buttons.append(button)

    
        self.zoom_slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 100, 500, 1)
        self.zoom_slider.set_value(int(self.config.get("group_image_zoom", "300").replace('%', '')))
        self.zoom_slider.set_hexpand(True)

    
        apply_button = Button(label="Apply", on_clicked=self.on_apply_clicked)

        # Layout
        layout = Box(orientation='vertical', spacing=10)
        layout.add(Label(label="Wallpaper:"))
        layout.add(self.wallpaper_file_chooser)
        layout.add(Label(label="Location:"))
        layout.add(self.location_entry)
        layout.add(Label(label="Scheme:"))
        layout.add(scheme_box)
        layout.add(Label(label="Theme Color:"))
        layout.add(theme_box)
        layout.add(apply_button)
        layout.add(Label(label="Group Image Zoom:"))
        layout.add(self.zoom_slider)
        layout.add(Label(label="Group Background Position:"))
        layout.add(background_position_box)

        self.children = layout

    def load_config(self):
        """Carrega o conteúdo do arquivo de configuração."""
        self.config = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if '=' not in line:
                        continue
                    key, value = line.strip().split("=", 1)
                    self.config[key] = value.strip('"')
                    
    def on_scheme_clicked(self, button):
        """Atualiza o valor de scheme baseado no botão clicado."""
        self.config['scheme'] = button.get_label()

    def on_theme_clicked(self, button):
        """Atualiza o valor de theme_color baseado no botão clicado."""
        self.config['theme_color'] = button.get_label()

    def on_background_position_clicked(self, button):
        """Atualiza o valor de background_position baseado no botão clicado."""
        self.config['background_position'] = button.get_label()

    def on_apply_clicked(self, button):
        """Ação ao clicar no botão Apply, salvando o arquivo e executando o script."""
        # Atualizar o arquivo de configuração
        self.config['wallpaper'] = self.wallpaper_file_chooser.get_filename()  # Obter o caminho do wallpaper
        self.config['location'] = self.location_entry.get_text()


        self.config['group_image_zoom'] = str(int(self.zoom_slider.get_value()))
        

        # Salvar o arquivo
        with open(self.config_file, "w") as f:
            for key, value in self.config.items():
                f.write(f'{key}="{value}"\n')

        # Executar o script bash
        self.run_bash_script()

    def open_file_chooser(self, button):
        """Abre um seletor de arquivos para escolher o wallpaper."""
        dialog = Gtk.FileChooserDialog(
            title="Select Wallpaper",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT
        )

        # Configurar a visualização de ícones
        dialog.set_preview_widget(Gtk.Image())  # Para mostrar uma imagem de pré-visualização
        dialog.set_preview_widget_active(True)  # Ativar a visualização
        dialog.set_current_folder(os.path.expanduser("~/Pictures"))  # Defina o diretório inicial desejado
        dialog.set_filter(self.create_image_filter())  # Adicione um filtro de imagem

        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            self.wallpaper_entry.set_text(filename)  # Definir o caminho da imagem selecionada

        dialog.destroy()

    def create_image_filter(self):
        """Cria um filtro para mostrar apenas arquivos de imagem."""
        filter_images = Gtk.FileFilter()
        filter_images.set_name("Image Files")
        filter_images.add_mime_type("image/png")
        filter_images.add_mime_type("image/jpeg")
        filter_images.add_mime_type("image/jpg")
        filter_images.add_mime_type("image/gif")
        filter_images.add_mime_type("image/bmp")
        filter_images.add_mime_type("image/webp")
        return filter_images


    def run_bash_script(self):
        """Executa o script bash após salvar o arquivo."""
        script = f"""
        sh /home/cadr/.config/matugen/theme_set.sh
        """
        subprocess.run(script, shell=True)

class MprisPlayerWidget(Box):
    def __init__(self):
        super().__init__(orientation='horizontal', spacing=10)

        self.album_art_size = 32  # Tamanho da imagem em pixels

        # Inicializar variáveis de metadados
        self.title_var = "Play some"
        self.artist_var = "godamn music"
        self.album_image = '/home/cadr/.config/fabric/default-cover.jpg'

        # Inicializar o playerctl
        self.player = Playerctl.Player()
        self.player.connect('playback-status::playing', self.on_play)
        self.player.connect('playback-status::paused', self.on_pause)
        self.player.connect('metadata', self.on_metadata)

        # Criar o widget do player com layout definido
        self.current_widget = self.create_player_widget()
        self.add(self.current_widget)

    def on_metadata(self, player, metadata):
        self.artist_var = metadata['xesam:artist'][0] if 'xesam:artist' in metadata.keys() else "Unknown Artist"
        self.title_var = metadata['xesam:title'] if 'xesam:title' in metadata.keys() else "Unknown Title"
        self.album_image = metadata['mpris:artUrl'] if 'mpris:artUrl' in metadata.keys() else "/home/cadr/.config/fabric/default-cover.jpg"


        self.title_var = (self.title_var[:25] + "...") if len(self.title_var) > 25 else self.title_var

        print(f"Now playing: {self.artist_var} - {self.title_var}")
        self.refresh_player_widget()  # Atualizar o widget com os novos dados

    def on_play(self, player, status):
        print(f"Playing at volume {player.props.volume}")
        # Atualizações que você quiser fazer no estado de play

    def on_pause(self, player, status):
        print(f"Paused the song: {player.get_title()}")
        # Atualizações que você quiser fazer no estado de pause

    def refresh_player_widget(self):
        if self.current_widget:
            self.remove(self.current_widget)
        self.current_widget = self.create_player_widget()
        self.add(self.current_widget)
        self.show_all()

        
    def create_player_widget(self):
        """Cria a interface do widget."""
        main_box = CenterBox(
            orientation='horizontal',
            name='music_box',
            end_children=[
                Box(
                    orientation='vertical',
                    spacing=2,
                    name = 'music-info',
                    h_align="end",
                    children=[
                        Label(name='music-title', h_align="end", label=self.title_var, font_size=16, max_chars_width= 10, ellipsization="end", line_wrap=None, chars_width=5),
                        Label(name='music-artist', h_align="end", label=self.artist_var, font_size=8)
                    ]
                ),
                Button(
                    v_align="center",
                    h_align="center",
                    child=CenterBox(
                        orientation="h",
                        name=f"album-cover",
                        h_align="center",
                        center_children=[Box(style=f"background-image:url('{self.album_image}');", name="albumc", v_align="center", h_align="end")],
                    ),
                    tooltip_text="Música atual",
                    on_clicked=lambda widget: print("Clique no cover")
                ),
            ]
        )
        return main_box

    
def setup_unix_socket(callback):
    """Configura o socket UNIX para receber atualizações."""
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove(SOCKET_PATH)
    except OSError:
        pass
    
    server_socket.bind(SOCKET_PATH)
    server_socket.listen(1)
    print(f"Listening on {SOCKET_PATH}")

    def accept_connection(*args):
        try:
            conn, _ = server_socket.accept()
            data = conn.recv(4096).decode('utf-8')
            if data:
                group_info = json.loads(data)
                callback(group_info)
            conn.close()
        except Exception as e:
            print(f"Erro no socket: {e}")
        return True  # Continua o loop de eventos

    # Usa GLib para repetir o check de novas conexões sem bloquear o loop principal
    GLib.io_add_watch(server_socket.fileno(), GLib.IO_IN, accept_connection)

# Widget de clima usando Fabricator
class WeatherWidget(EventBox):
    def __init__(self, latitude: float, longitude: float, **kwargs):
        super().__init__(**kwargs)
        self.latitude = latitude
        self.longitude = longitude

        self.label = Label(label="Carregando clima...", style="font-weight: 900")
        self.children = self.label

        # Carregar o clima na inicialização
        self.update_weather()

        # Conectar o evento de clique
        self.connect("button-press-event", self.on_click)

    def fetch_weather(self):
        try:
            response = requests.get(f"https://wttr.in/{self.latitude},{self.longitude}?format=%c+%t")

            return response.text.strip().replace(' +', '') if response.status_code == 200 else "Erro"
        except Exception as e:
            return f"Erro: {e}"

    def update_weather(self):
        weather = self.fetch_weather()
        self.label.set_label(weather)

    def on_click(self, widget, event):
        self.update_weather()
        return True

# Classe do GroupTaskList
def find_desktop_app_by_class(window_class: str) -> DesktopApp | None:
    return next(
        (app for app in get_desktop_applications()
         if app.icon_name == window_class or app.window_class == window_class),
        None
    )


def toggle_window(window_id, group_name):
    window_info = c.window[window_id].info()
    current_window = c.window.info()

    # Muda para o grupo especificado se os grupos forem diferentes
    if window_info['group'] != current_window['group']:
        c.group[group_name].toscreen()
        return  # Sai da função após mudar de grupo

    # Se a janela estiver minimizada, desminimize-a
    if window_info['minimized']:
        c.window[window_id].toggle_minimize()
    # Se a janela não estiver focada, foca-a
    elif current_window['name'] != window_info['name']:
        c.window[window_id].focus()
    else:
        # Se a janela estiver focada, minimiza-a
        c.window[window_id].toggle_minimize()

        
def handle_click(window, group_name):
    #print(c.window.info())
    #print(c.group[group_name].info()) 
    #print(c.window[window_id].info())
    #print(c.group[group_name].info())
    window_id = window.get('wid')
    toggle_window(window_id, group_name)

    

def get_window_icon(window, group_name, icon_size, default_icon="application-default-icon"):
#this is a qtile specific window_icon widget. It should work on Wayland and X. 
    window_id = window.get('wid')
    window_class_list = window.get("class", [None])

    window_class = window_class_list[0]
    app = find_desktop_app_by_class(window_class)
    
    if not app and len(window_class_list) > 1:
        #Wayland doesnt send two classes, this is necessary because some icons
        #class names  are stored in the second string on Xorg.
        window_class = window_class_list[1]
        app = find_desktop_app_by_class(window_class)

    if app:
        pixbuf = app.get_icon_pixbuf(size=icon_size, default_icon=default_icon)
    else:
        icon_path = os.path.join("/home/cadr/.config/qtile/task_icons/", f"{window_class.lower()}")
        
        if not os.path.exists(icon_path):
            icon_path = "/home/cadr/.config/qtile/task_icons/unknown_app.png"
        
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, icon_size, icon_size)

    return Button(
        v_align="center",
        h_align="center",
        child=CenterBox(
            orientation="h",
            name=f"win-{window.get('state')}",
            v_align="center",
            h_align="center",
            center_children=[Image(pixbuf=pixbuf, v_align="center", h_align="center")],
        ),
        tooltip_text=app.description if app else "a",
        on_clicked=lambda widget: handle_click(window, group_name)
    )


class GroupTaskList(Box):
    def __init__(self, group_filter=None, icon_size=16, **kwargs):
        super().__init__(**kwargs)
        self.group_filter = group_filter
        self.icon_size = icon_size
        self.groups = {}
        self.add_style_class = "group_box"
        self.set_name("group_box")
        self.update_groups()

    def update_groups(self):
        self.clear()
        self.add_style_class = "group_box"
        for group_name, group_data in self.groups.items():
            if self.group_filter and group_name not in self.group_filter:
                continue

            group_label = Label(label=f" ", style="font-weight: bold;")

            if group_data["focused"]:
                group_tag = "group_focused"
            else:
                group_tag = "groups"

            icon_boxes = []
            for win in group_data["windows"]:
                icon_widget = get_window_icon(win, group_name, self.icon_size)

                if icon_widget:
                    icon_boxes.append(icon_widget)
                else:
                    icon_boxes.append(Label(label=win.get("name", "Unknown")))

            # Usar o CenterBox para centralizar o conteúdo do grupo
            group_box = CenterBox(
                name=group_tag,
                start_children=Box(
                    spacing=4,
                    orientation="h",
                    children=[group_label],  # Pode adicionar algo no início se necessário
                ),
                center_children=Box(
                    spacing=4,
                    orientation="h",
                    children=icon_boxes,  # Ícones centralizados
                ),
                end_children=Box(
                    spacing=4,
                    orientation="h",
                    children=[],  # Pode adicionar algo no final se necessário
                ),
            )

            self.add(group_box)

        self.queue_draw()


        

    def update_from_data(self, data):
        self.groups = data
        self.update_groups()

    def clear(self):
        self.children = []


class VolumeWidget(Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.audio = Audio()

        self.progress_bar = CircularProgressBar(
            name="volume-progress-bar", pie=True, size=24
        )

        self.event_box = EventBox(
            events="scroll",
            child=Overlay(
                child=self.progress_bar,
                overlays=Label(
                    label="",
                    style="margin: 0px 6px 0px 0px; font-size: 12px",
                ),
            ),
        )

        self.audio.connect("notify::speaker", self.on_speaker_changed)
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add(self.event_box)

    def on_scroll(self, _, event):
        match event.direction:
            case 0:
                self.audio.speaker.volume += 8
            case 1:
                self.audio.speaker.volume -= 8
        return

    def on_speaker_changed(self, *_):
        if not self.audio.speaker:
            return
        self.progress_bar.value = self.audio.speaker.volume / 100
        self.audio.speaker.bind(
            "volume", "value", self.progress_bar, lambda _, v: v / 100
        )
        return

# StatusBar com integração do socket
class StatusBar(Window):
    def __init__(self):
        super().__init__(
            name="bar_",
            #geometry="top",
            type_hint="dock",
            taskbar_hint=True,
            pager_hint=True,
            anchor="left top right",
            layer="top",
            #anchor="left top right",
            #margin="10px 10px -2px 10px",
            exclusivity="auto",
            visible=False,
            all_visible=False,
            size=(1920, 50),
            #margin="0px 10px -2px 10px",
            open_inspector=True,
        )
        self.group_task_list = GroupTaskList(
            group_filter=["1", "2", "3", "4"],
            icon_size=16,
        )

        self.settings_button = Button(label="⚙", on_clicked=self.open_config_editor)
        self.config_editor_window = None

        self.music_player = MprisPlayerWidget()

        self.system_tray = SystemTray(name="system-tray", spacing=4)
        #self.system_tray = SystemTrayWidget()
        self.date_time = DateTime(name="date-time", interval=60000, formatters=["🌟 %Y   ⌚ %H:%M   ✨ %d de %B   "])
        # self.weather_widget = WeatherWidget(latitude=-29.9216045, longitude=-51.1799525)

        self.ram_progress_bar = CircularProgressBar(
            name="ram-progress-bar", pie=True, size=24
        )
        self.cpu_progress_bar = CircularProgressBar(
            name="cpu-progress-bar", pie=True, size=24
        )
        self.progress_bars_overlay = Overlay(
            child=self.ram_progress_bar,
            overlays=[
                self.cpu_progress_bar,
                Label("", style="margin: 0px 6px 0px 0px; font-size: 12px"),
            ],
        )

        self.status_container = Box(
            name="widgets-container",
            spacing=4,
            orientation="h",
            children=self.progress_bars_overlay,
        )
        self.status_container.add(VolumeWidget()) if AUDIO_WIDGET is True else None

        self.children = CenterBox(
            name="bar-inner",
            start_children=Box(
                name="start-container",
                spacing=4,
                orientation="h",
                children=[self.settings_button, self.group_task_list]
            ),
            center_children=Box(
                name="center-container",
                spacing=4,
                orientation="h",
                children=[self.date_time,
                          #self.weather_widget
                          ],
            ),
            end_children=Box(
                name="end-container",
                spacing=4,
                orientation="h",
                children=[
                    self.music_player,
                    self.status_container,
                    self.system_tray,
                ],
            ),
        )

        # Configura o socket UNIX para receber dados e atualizar o widget
        #setup_unix_socket(self.update_group_data)

        invoke_repeater(1000, self.update_progress_bars)

        self.show_all()

        # Conecta o evento de mudança de speaker
        self.mine_audio = Audio()
        self.mine_audio.connect("notify::speaker", self.speaker_changed)

    def open_config_editor(self, button):
        """Abre o editor de configuração ou fecha se já estiver aberto."""
        config_file = "/home/cadr/.config/matugen/vars"
        
        # Verifica se a janela de configuração já está aberta
        if self.config_editor_window is not None and self.config_editor_window.is_visible():
            self.config_editor_window.hide() 
        else:
            # Cria uma nova janela de configuração
            self.config_editor_window = ConfigEditorWindow(config_file)
            self.config_editor_window.show_all()

            # Coloca a janela de configurações abaixo do botão
            # self.config_editor_window.set_transient_for(self.settings_button.get_window())  # Torna a janela dependente do botão
            self.config_editor_window.show()  # Mostra a janela

    def update_progress_bars(self):
        self.ram_progress_bar.value = psutil.virtual_memory().percent / 100
        self.cpu_progress_bar.value = psutil.cpu_percent() / 100
        return True

    def speaker_changed(self):
        """Ação quando o speaker é alterado."""
        self.audio_popup = OSDContainer("me")
        self.config_editor_window = ConfigEditorWindow(config_file)
        self.config_editor_window.show_all()
        self.config_editor_window.show()  

        
def callback_function(file_monitor, file, other_file, event):
    file_path = file.get_path()
    """Callback para atualizar os dados dos grupos."""
    if os.path.getsize(file_path) > 0:
        with open(file_path, 'r') as f:
            bar.group_task_list.update_from_data(json.load(f))

if __name__ == "__main__":


    def main_on_speaker_changed():
        config_editor_window = ConfigEditorWindow(config_file)
        config_editor_window.show_all()
        config_editor_window.show()
        

    bar = StatusBar()
    Audio().connect("notify::speaker", main_on_speaker_changed)
    

        
    

#    system_overlay = OSDContainer()

    app = Application("bar", bar)
    
    groupsinformation = monitor_file("/tmp/group_info.json", "watch_moves")
    groupsinformation.connect("changed", callback_function)

    def apply_style(app: Application):
        #logger.info("[Main] CSS applied")
        return app.set_stylesheet_from_file(get_relative_path("matugen.css"))
    
    app.set_stylesheet_from_file(get_relative_path("matugen.css"))

    file = monitor_file(get_relative_path("matugen.css"))
    file.connect("changed", lambda *args: apply_style(app))
    
    app.run()
