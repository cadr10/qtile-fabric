import os
import re
import subprocess
import platform
import sys
import json
import time
import threading

import json
import socket
import asyncio
import msgpack



from libqtile import bar, layout, widget, qtile, hook
from libqtile.config import Click, Drag, Group, Key, Match, Screen, ScratchPad, DropDown
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal
from libqtile.log_utils import logger
from libqtile.backend.wayland import InputConfig
from libqtile.config import EzKey
from widgets.group_icons_git.group_icons import GroupTaskList


main = None
from graphical_notifications import Notifier

from date_time import DateTimeWidget






def hide_show_bar(qtile):
    """Toggle the eww bar."""
    script = os.path.expanduser('~/.config/qtile/scripts/toggleBar.sh')
    subprocess.call([script])
    gap = qtile.screens[0].top
    if gap.size == 0:
        gap.size = 48
    else:
        gap.size = 0

scratchpad_tauon_window_count = 0
def check_tauon_scratchpad(client):
    global scratchpad_tauon_window_count
    if Match(wm_class="Tauon Music Box").compare(client):
        scratchpad_tauon_window_count += 1
        if scratchpad_tauon_window_count == 2:
            scratchpad_tauon_window_count = 0
            return True
    return False



def find_or_run2(app, matchd):
  #  @lazy.function
    def __inner(qtile):
        for window in qtile.cmd_windows():
            file = open("/home/cadr/car.txt", "w")
            file.write(str(qtile.current_screen.group))
            file.close
                
                    
    return __inner



def find_or_run(app, wm_class):
    def __inner(qtile):

        for window in qtile.windows_map.values():

            if hasattr(window, "cmd_match") and window.cmd_match(Match(wm_class=wm_class)):

                qtile.current_screen.set_group(window.group)

                window.focus(False)

                return

        qtile.spawn(app)

    return __inner




#qtile.cmd_spawn('ags -c ~/.config/ags/config.js')



#qtile.cmd_spawn("sh -c 'pgrep sxhkd || sxhkd'")




mod = "mod4"
terminal = guess_terminal()




sticky_windows = []

@lazy.function
def toggle_sticky_windows(qtile, window=None):
    if window is None:
        window = qtile.current_screen.group.current_window
    if window in sticky_windows:
        sticky_windows.remove(window)
    else:
        sticky_windows.append(window)
    return window

@hook.subscribe.setgroup
def move_sticky_windows():
    for window in sticky_windows:
        window.togroup()
    return

@hook.subscribe.client_killed
def remove_sticky_windows(window):
    if window in sticky_windows:
        sticky_windows.remove(window)



#for i in groups:
#    keys.append(Key([mod], i.name, lazy.function(go_to_group(i.name))))

keys = [

    Key([mod], "Return", lazy.spawn("alacritty"), desc="terminal"),

    Key([mod], "space", lazy.spawn("rofi -show drun"), desc="Wofi Launcher"),

    Key(["mod1"], "space", lazy.spawn("ulauncher"), desc="ulauncher-toggle"),


        # A list of available commands that can be bound to keys can be found
    # at https://docs.qtile.org/en/latest/manual/config/lazy.html
    # Switch between windows
    
    Key([], "XF86AudioRaiseVolume", lazy.spawn("amixer set Master 5%+"), desc="Options"),

    Key([], "XF86AudioLowerVolume", lazy.spawn("amixer set Master 5%-"), desc="Options"),

   # Key([mod], "F8", lazy.spawn("sh /home/cadr/.config/eww/scripts/scripts systemopt"), desc="Options"),


#    Key([mod], "F7", run_or_raise(), desc="Options"),

    
    Key([mod], "h", lazy.layout.left(), desc="Move focus to left"),
    Key([mod], "l", lazy.layout.right(), desc="Move focus to right"),
    Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
    Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
    Key([mod], "Tab", lazy.group.next_window(), desc="Move window focus to other window"),
    # Move windows between left/right columns or move up/down in current stack.
    # Moving out of range in Columns layout will create new column.
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Move window to the left"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Move window to the right"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
    # Grow windows. If current window is on the edge of screen and direction
    # will be to screen edge - window would shrink.
    Key([mod, "control"], "h", lazy.layout.grow_left(), desc="Grow window to the left"),
    Key([mod, "control"], "l", lazy.layout.grow_right(), desc="Grow window to the right"),
    Key([mod, "control"], "j", lazy.layout.grow_down(), desc="Grow window down"),
    Key([mod, "control"], "k", lazy.layout.grow_up(), desc="Grow window up"),
    Key([mod], "n", lazy.layout.normalize(), desc="Reset all window sizes"),
    Key([mod], "d", lazy.window.toggle_floating(), desc="toggle floating"),
    Key([mod], "f", lazy.window.toggle_fullscreen(), desc="toggle fullscreen"),
    Key([mod], "s", toggle_sticky_windows(), desc="toggle stickness"),
    
    # Toggle between split and unsplit sides of stack.
    # Split = all windows displayed
    # Unsplit = 1 window displayed, like Max layout, but still with
    # multiple stack panes
    Key(
        [mod, "shift"],
        "Return",
        lazy.layout.toggle_split(),
        desc="Toggle between split and unsplit sides of stack",
    ),

    # Toggle between different layouts as defined below
    #Key([mod], "space", lazy.next_layout(), desc="Toggle between layouts"),
    Key([mod, "shift"], "q", lazy.window.kill(), desc="Kill focused window"),
    Key([mod, "shift"], "r", lazy.reload_config(), desc="Reload the config"),
    Key([mod, "shift"], "m", lazy.shutdown(), desc="Shutdown Qtile"),
   

    #Programs
    #Key([mod], "w", lazy.group['sp'].dropdown_toggle('browser'), desc="Spawn a browser window"),
    Key([mod], "w", lazy.function(find_or_run("firefox", "firefox")), desc='Open Browser'),
    #Key([mod], "c", lazy.spawn('tauon'), desc="Music Player"),
    Key([mod], "c", lazy.group['sp'].dropdown_toggle('tauon')),
   # Key([mod], "a", lazy.spawn('kitty -e ranger'), desc='Open Ranger Terminal'),

    Key([mod], "b", lazy.function(hide_show_bar)),

    #Key([mod], "x", run_raise('lutris', 'lutris'), desc='Open Browser'),

    Key([mod], "z", lazy.function(find_or_run("ferdi", "ferdi")))
   
]



keymap = {
    'M-<delete>': lazy.next_layout(),
    'M-<left>': lazy.layout.left(),
    'M-<down>': lazy.layout.down(),
    'M-<up>': lazy.layout.up(),
    'M-<right>': lazy.layout.right(),
    'M-S-<left>': lazy.layout.move_left(),
    'M-S-<right>': lazy.layout.move_down(),
    'M-S-<up>': lazy.layout.move_up(),
    'M-S-<right>': lazy.layout.move_right(),
    'M-A-<left>': lazy.layout.integrate_left(),
    'M-A-<down>': lazy.layout.integrate_down(),
    'M-A-<up>': lazy.layout.integrate_up(),
    'M-A-<right>': lazy.layout.integrate_right(),
    'M-c': lazy.layout.mode_horizontal(),
    'M-v': lazy.layout.mode_vertical(),
    'M-S-c': lazy.layout.mode_horizontal_split(),
    'M-S-v': lazy.layout.mode_vertical_split(),
    'M-<prior>': lazy.layout.grow_width(30),
    'M-<next>': lazy.layout.grow_width(-30),
    'M-S-<prior>': lazy.layout.grow_height(30),
    'M-S-<next>': lazy.layout.grow_height(-30),
    'M-C-5': lazy.layout.size(500),
    'M-C-8': lazy.layout.size(800),
    'M-n': lazy.layout.reset_size(),
}
keys += [EzKey(k, v) for k, v in keymap.items()]




#groups = [Group(i) for i in "123456789"]

def go_to_group(qtile, group_name, screen):
    #lazy.group[group_name].toscreen()
    
    qtile.focus_screen(screen)
    qtile.groups_map[group_name].toscreen()

    #qtile.warp_to_screen()





if qtile.core.name == "x11":
    workspaces = [ 
    {"name": "F1", "screen": 1},
    {"name": "F2", "screen": 1},
    {"name": "F3", "screen": 1},
    {"name": "1"},
    {"name": "2"},
    {"name": "3"},
    {"name": "4", "matches": [Match(wm_class="spotify\|vesktop")]},
   # {"name": "5"},
    ]


    term = "urxvt"
elif qtile.core.name == "wayland":
    workspaces = [ 
    {"name": "F1", "screen": 0},
    {"name": "F2", "screen": 0},
    {"name": "F3", "screen": 0},
    {"name": "1", "screen": 1},
    {"name": "2", "screen": 1},
    {"name": "3", "screen": 1, "matches": [Match(wm_class="spotify\|vesktop")]},
    {"name": "4", "screen": 1},
   # {"name": "5", "screen": 1},
    ]





dropdown_conf = {
    'opacity': 1,
    'warp_pointer': False,
    'height': 0.45,
}

groups = []

groups.append(
    ScratchPad('sp', [
            DropDown(
                'tauon',
                'tauon',     
                match=Match(func=check_tauon_scratchpad),
                on_focus_lost_hide= False,
                height=0.6,
                width=0.4,
                y=0.35,
                x=0.595,
            ),

            DropDown(
                'browser',
                'qutebrowser',     
                match=Match(wm_instance_class="qutebrowser"),                
        **dropdown_conf
            ),



]))


for workspace in workspaces:
    matches = workspace["matches"] if "matches" in workspace else None
    screen = workspace["screen"] if "screen" in workspace else 0
    spawn = workspace["spawn"] if "spawn" in workspace else None
    key = workspace["name"]
    # screen_affinity sounds like specifying a screen but doesn't work
    groups.append(
        Group(workspace["name"], matches=matches, spawn=spawn, screen_affinity=screen)
    )
    keys.append(Key([mod], key, lazy.function(go_to_group, workspace["name"], screen)))
    keys.append(Key([mod, "shift"], key, lazy.window.togroup(workspace["name"])))

#eDP-1, HDMI-A-1

layouts = [
    layout.Plasma(margin=10,border_width=2),
#    layout.Bsp(),
#    layout.Columns(border_focus_stack=["#d75f5f", "#8f3d3d"], border_width=10),
    layout.Max(),

]




widget_defaults = dict(
    font="sans",
    fontsize=12,
    padding=8,
)
#extension_defaults = widget_defaults.copy()


music = widget.Mpris2(
                    name='Feishin',
                    #objname="org.mpris.MediaPlayer2.tauon",
                    format = '<b>🎵   {xesam:title}</b>   {xesam:artist}',
                    #scroll_chars=None,
                    stopped_text='No music playing :(',
                    background = "334455",
                    padding = 12,
                    fontsize = 12,
                    scroll=True,
                    scroll_fixed_width=True,
                    width=250,
                )



widget_defaults = dict(
    font='sans',
    fontsize=12,
    padding=3,
)




screenold_config = {
    "wallpaper": "/home/cadr/Imagens/wallpaper/366398.jpg",
    "top": bar.Bar(
        [
            
            widget.Spacer(length=8),
            widget.CurrentLayoutIcon(scale=0.5),
            widget.Spacer(length=15),
 #           group_tasklist,
            
            GroupTaskList(group_name='1'),
            widget.Spacer(length=2),
            GroupTaskList(group_name='2'),
            widget.Spacer(length=2),
            GroupTaskList(group_name='3'),
            widget.Spacer(length=2),
            GroupTaskList(group_name='4'),
            widget.Spacer(length=2),
            GroupTaskList(group_name='5'),
 

            widget.Spacer(length=209),
           

#            widget.Prompt(),
           # widget.WindowName(),
           # widget.Spacer(length=bar.STRETCH),
            widget.Clock(format="<b>🌟 %Y   ⌚ %H:%M   ✨ %d de %B</b>"),
            widget.Wttr(format='<b>%c %t</b>', location={'-29.95426027072933,-51.176779292942925': 'Ingå'}),
            widget.Spacer(length=56),
            
            music,
            widget.Wlan(format="🌐   {essid}   🛜   {percent:2.0%}"),
            widget.Bluetooth(),
            widget.Spacer(length=2),
            widget.Spacer(length=bar.STRETCH),
            widget.Volume(emoji=False, background="334455", fmt='<b>    🔊    {}    </b>'),
            widget.Spacer(length=15),
            #widget.Systray(),
            widget.Spacer(length=12),
            
        ],
        40,
    ),
}

screen1_config = {
    "wallpaper": "/home/cadr/Imagens/wallpaper/366398.jpg",
    "top": bar.Bar(
        [
            widget.Spacer(length=2)
        ],
        size = 1,
    ),
}


# Configuração para a segunda tela
screen2_config = {
    "top": bar.Bar(
        [
            widget.CurrentLayout(),
            widget.GroupBox(visible_groups=['F1', 'F2', 'F3']),
           # widget.Systray(),
           # widget.Prompt(),
            widget.TaskList(),
            widget.Chord(
                chords_colors={
                    "launch": ("#ff0000", "#ffffff"),
                },
                name_transform=lambda name: name.upper(),
            ),
            widget.Clock(format="%a %d %b %Y %H:%M"),
        ],
        size = 1,
    ),
}

# Lista de telas usando as configurações


if qtile.core.name == "x11d":

   # print("cool")
    screens = [ Screen(**screen1_config), Screen(**screen2_config) ]

    
elif qtile.core.name == "waylandd":
    #qtile.cmd_spawn('kanshi &')
    qtile.spawn("sh -c 'pgrep kanshi || kanshi'")
    screens = [
        Screen(**screen1_config),  # Primeira tela
        Screen(**screen2_config),  # Segunda tela
    ]


screens = [ Screen(**screen1_config), Screen(**screen2_config) ]


# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

dgroups_key_binder = None
dgroups_app_rules = []  # type: list
follow_mouse_focus = False
bring_front_click = True
cursor_warp = False
focus_on_window_activation = "focus"
floating_layout = layout.Floating(
    float_rules=[
        # Run the utility of `xprop` to see the wm class and name of an X client.
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
        Match(title="emacs-run-launcher"),
        Match(wm_class="protonvpn-app"),
    ]
)
auto_fullscreen = True
#focus_on_window_activation = "urgent"
#reconfigure_screens = True

# If things like steam games want to auto-minimize themselves when losing
# focus, should we respect this or not?
auto_minimize = True

# When using the Wayland backend, this can be used to configure input devices.
#wl_input_rules = None


floating_types = ["notification", "toolbar", "splash", "dialog",
                  "utility", "menu", "dropdown_menu", "popup_menu", "tooltip,dock",
                  ]

floating_class = ["easyeffects", "krunner"]


wmname = "LG3D"


wl_input_rules = {

    "type:keyboard": InputConfig(kb_layout="br"),
    "type:pointer":  InputConfig(accel_profile="flat"),

    }

last_write_time = 0
write_interval = 0.1 
group_info_cache = {}

def async_send_group_info_socket():
    global last_write_time, group_info_cache
    destination="both"
    #time.sleep(1)
    group_info = {}

    for group_name, group in qtile.groups_map.items():
        windows_info = []

        for win in group.windows:
            #logger.exception(win.static)
            if win == qtile.current_window:
                window_state = "focused"
            elif win.minimized:
                window_state = "minimized"
            elif win.floating:
                window_state = "floating"
            else:
                window_state = "unfocused"
            windows_info.append({
                "name": win.name,
                "class": win.get_wm_class(),
                "state": window_state,
                "wid": win.wid,
            })

        group_info[group_name] = {
            "focused": group == qtile.current_group,
            "windows": windows_info,
            "screen": group.screen.index if group.screen else None,
        }

    if group_info != group_info_cache: 
        group_info_cache = group_info

        if destination in ("file", "both"):
            with open("/tmp/group_info.json", "w") as f:
                json.dump(group_info, f, indent=4)
                #msgpack.packb(group_info)

        if destination in ("socket", "both"):
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect("/tmp/fabric_qtile_socket")
                sock.sendall(json.dumps(group_info).encode('utf-8'))
                
        last_write_time = time.time()

@hook.subscribe.client_new
@hook.subscribe.client_killed
@hook.subscribe.client_managed
@hook.subscribe.client_urgent_hint_changed
@hook.subscribe.setgroup
@hook.subscribe.group_window_add
@hook.subscribe.current_screen_change
@hook.subscribe.changegroup
@hook.subscribe.client_focus
def write_group_info(*args):
    global last_write_time
    current_time = time.time()
    if current_time - last_write_time >= write_interval:
        threading.Thread(target=async_send_group_info_socket).start()

@hook.subscribe.startup
def bring_bar_front(*args):
    for window in qtile.windows_map.values():
        if window.window.get_wm_class() and window.window.get_wm_class()[0] == "bar.py":
            logger.exception("NEW MATCH")
        else:
            qtile.spawn("bash -c 'python /home/cadr/.config/fabric/bar.py'")
            #window.focus(warp=True)



@hook.subscribe.startup
def autostart():
    qtile.spawn('/home/cadr/.config/00-comon-files/start.sh', shell=True)
