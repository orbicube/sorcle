import pyglet
import pathlib
import sys, os
from os import path
from random import choice, randint
from glob import glob
import requests

from text_fix import ArcadeTextLayoutGroup

if getattr(sys, 'frozen', False):
    w_dir = pathlib.Path(sys._MEIPASS).parent
else:
    w_dir = os.path.dirname(os.path.abspath(__file__))
pyglet.resource.path = [str(w_dir)]

import tomllib
with open(path.join(w_dir, "settings.toml"), "rb") as f:
    settings = tomllib.load(f)
    
    if not settings["spreadsheet"]["api_key"]:
        raise ValueError("Couldn't find an API key in settings.toml")

def get_text_color(color):
    color_intensity = (color[0]*.299 + color[1]*.587 + color[2]*.114)
    if color_intensity > 149:
        return (10, 10, 10)
    else:
        return (255, 255, 255)

class Wedge(pyglet.shapes.Sector):

    def __init__(self, name, sub, extras, start_angle, angle, color, 
        wedge_group, text_group, batch):
        super().__init__(x = 500, y = 500, radius=495,
            start_angle = start_angle, angle = angle, color = color,
            group = wedge_group, batch=batch)

        self.name = name
        self.sub = sub
        self.extras = extras

        # Trim name if too long
        if len(name) > 23:
            disp_name = name[:21] + "..."
        else:
            disp_name = name

        # Adjust font size for smaller wedges
        if angle < 1.6: font_floor = 6
        elif angle < 3.2: font_floor = 10
        else: font_floor = 14
        font_size = angle * .70 + font_floor
        if font_size > 23:
            font_size = 23

        self.label = pyglet.text.Label(
            text=disp_name, font_name=settings["wheel"]["font"], x=500, y=500, 
            font_size=font_size, color=get_text_color(color), width=485,
            align='right', anchor_y='center', group=text_group, batch=batch,
            rotation=(-(start_angle+(start_angle+angle))/2))

    def rotate(self, velocity):
        self.rotation = (self.rotation + velocity) % 360
        self.label.rotation = (self.label.rotation + velocity) % 360

        if self.start_angle == 0.0:
            return self.rotation < self.angle
        else:
            return (self.rotation - self.start_angle) % 360 < self.rotation

class Wheel:
    
    def __init__(self, center_sprite, batch):
        self.wedges = []
        self.spinning = False
        self.finished = False
        self.idle = True
        self.selected = {"name": "", "sub": "", "extras": [],
            "color": (0,0,0,0)}

        self.batch = batch
        self.wedge_group = pyglet.graphics.Group(order=0)
        self.text_group = pyglet.graphics.Group(order=1)

        self.center_sprite = center_sprite

        self.colors = []
        for color in settings["wheel"]["colors"]:
            self.colors.append(tuple(color))

        self.import_spreadsheet()


    def import_spreadsheet(self):
        self.wedges = []

        # Setup list of columns to scan
        s_config = settings["spreadsheet"]
        columns_to_scan = [s_config["column"]]
        if s_config["sub_column"]:
            columns_to_scan.append(s_config["sub_column"])
        if s_config["extra_columns"]:
            for c in s_config["extra_columns"]:
                columns_to_scan.append(c)

        ranges = [f"{s_config['sheet']}!{c}{s_config['row']}:{c}" for c in columns_to_scan]

        params = {
            "key": s_config["api_key"],
            "ranges": ranges
        }
        r = requests.get(("https://sheets.googleapis.com/v4/spreadsheets/"
            f"{s_config['id']}/values:batchGet"), params=params)
        columns = r.json()["valueRanges"]

        # Handle resulting 
        rows = columns[0]["values"]
        columns.pop(0)
        if s_config["sub_column"]:
            sub_rows = columns[0]["values"]
            columns.pop(0)
        if s_config['extra_columns']:
            extra_rows = []
            for c in s_config["extra_columns"]:
                extra_rows.append(columns[0]["values"])
                columns.pop(0)

        # Grab all values, filter out empty and handle dupe logic
        temp_wedges = []
        for row in rows:
            if row:
                try: sub = sub_rows[rows.index(row)][0]
                except: sub = ""
                try: extras = [x[rows.index(row)][0] for x in extra_rows]
                except: extras = []

                wedge_dict = {
                    "name": row[0], "sub": sub, "extras": extras }

                prev_wedges = [w["name"] for w in temp_wedges]
                # Filter out dupe games if setting is true
                if settings["wheel"]["remove_dupes"]:
                    if row[0] not in prev_wedges:
                        temp_wedges.append(wedge_dict)
                # Otherwise, put the dupes next to each other to combine later
                else:
                    if row[0] in prev_wedges and settings["wheel"]["combine_dupes"]:
                        temp_wedges.insert(prev_wedges.index(row[0]),
                            wedge_dict)
                    else:
                        temp_wedges.append(wedge_dict)

        # Calculate angle for wedges
        wedge_num = len(temp_wedges)
        angle_per_wedge = 360 / wedge_num

        curr_angle = 0.0
        curr_wedge = 0
        prev_color = (0,0,0)
        for wedge in temp_wedges:

            dupe_wedge = False
            if not settings["wheel"]["remove_dupes"]:
                if settings["wheel"]["combine_dupes"]:
                    if curr_wedge > 0:
                        if wedge["name"] == self.wedges[-1].name:
                            dupe_wedge = True
                            self.wedges[-1].angle += angle_per_wedge
                            self.wedges[-1].label.rotation -= (angle_per_wedge / 2)

            if not dupe_wedge:
                # Ensure no color dupes, can't do random.sample() unfortunately
                # list[:] copies
                valid_colors = self.colors[:]
                if curr_wedge > 0:
                    valid_colors.remove(prev_color)
                # Make sure first and last aren't the same
                if curr_wedge == wedge_num-1 and self.wedges[0].color[:-1] != prev_color:
                    if len(valid_colors) > 1:
                        valid_colors.remove(self.wedges[0].color[:-1])
                color = choice(valid_colors)
                prev_color = color

                self.wedges.append(Wedge(name=wedge["name"], sub=wedge["sub"],
                    extras=wedge["extras"], start_angle=curr_angle,
                    angle=angle_per_wedge, color=color, batch=self.batch,
                    wedge_group=self.wedge_group, text_group=self.text_group))

            curr_angle += angle_per_wedge
            curr_wedge += 1


    def rotate(self, velocity):
        if settings["center"]["rotate"]:
            self.center_sprite.rotation = (
                self.center_sprite.rotation + velocity) % 360

        for wedge in self.wedges:
            is_selected = wedge.rotate(velocity)
            if self.spinning and is_selected:
                if self.selected["name"] != wedge.name:
                    self.selected["name"] = wedge.name
                    self.selected["sub"] = wedge.sub
                    self.selected["extras"] = wedge.extras
                    self.selected["color"] = wedge.color[:-1]


class Sorcle(pyglet.window.Window):

    def __init__(self, config):
        super().__init__(width = 1200, height = 1000, caption = "sorcle",
            config = config, style='transparent')

        pyglet.text.layout.TextLayout.group_class = ArcadeTextLayoutGroup

        icon = pyglet.image.load(path.join(w_dir, settings["center"]["file"]))
        self.set_icon(icon)

        # For crisp pixel scaling
        if settings["window"]["nearest_neighbour"]:
            pyglet.image.Texture.default_mag_filter = pyglet.gl.GL_NEAREST
            pyglet.image.Texture.default_min_filter = pyglet.gl.GL_NEAREST

        #self.fps_display = pyglet.window.FPSDisplay(self)
        self.batch = pyglet.graphics.Batch()

        self.initial_velocity = 25

        self.sprite_group = pyglet.graphics.Group(order=3)
        if settings["center"]["file"].rsplit(".")[1] == "gif":
            center = pyglet.resource.animation(settings["center"]["file"])
            for f in center.frames:
                f.image.anchor_x = f.image.width//2
                f.image.anchor_y = f.image.height//2
        else:
            center = pyglet.image.load(
                path.join(w_dir, settings["center"]["file"]))
            center.anchor_x = center.width//2
            center.anchor_y = center.height//2
        self.center_sprite = pyglet.sprite.Sprite(center,
            x=500, y=500, group=self.sprite_group, batch=self.batch)
        self.center_sprite.update(scale=settings["center"]["scale"])

        self.wheel = Wheel(self.center_sprite, self.batch)

        # Position pointer, change anchor keeping centered regardless of size
        if settings["pointer"]["file"].rsplit(".")[1] == "gif":
            pointer = pyglet.resource.animation(settings["pointer"]["file"])
            for f in pointer.frames:
                f.image.anchor_x = f.image.width//2
                f.image.anchor_y = f.image.height//2
        else:
            pointer = pyglet.image.load(
                path.join(w_dir, settings["pointer"]["file"]))
            pointer.anchor_x = pointer.width//2
            pointer.anchor_y = pointer.height//2
        self.pointer_sprite = pyglet.sprite.Sprite(pointer,
            x=settings["pointer"]["x_pos"], y=settings["pointer"]["y_pos"],
            group=self.sprite_group, batch=self.batch)
        self.pointer_sprite.update(scale=settings["pointer"]["scale"])

        self.sound = pyglet.media.load(
            path.join(w_dir, settings["tick"]["file"]), streaming=False)
        self.player = None

        self.winner_group = pyglet.graphics.Group(order=5)
        self.winner_label = None
        self.background_group = pyglet.graphics.Group(order=4)
        self.winner_bg = None
        self.sub = None


    def handle_win(self, winner):
        with open(path.join(w_dir, "winner.txt"), 'w', encoding='utf-8') as f:
            f.write(winner["name"])

        if winner["sub"]:
            with open(path.join(w_dir, "sub.txt"), 'w', encoding='utf-8') as f:
                f.write(winner["sub"])
        else:
            with open(path.join(w_dir, "sub.txt"), 'w', encoding='utf-8') as f:
                f.write("")

        extra_files = glob(path.join(w_dir,"extra*.txt"))
        for file in extra_files:
            with open(file, 'w') as f:
                f.write("")
        if winner["extras"]:
            ex_count = 1
            for column in winner["extras"]:
                with open(path.join(w_dir, f"extra{ex_count}.txt"), 'w', encoding='utf-8') as f:
                    f.write(column)
                ex_count += 1

        if not settings["wheel"]["suppress_win"]:
            finished = pyglet.media.load(
                path.join(w_dir, settings["finished"]["file"]))
            finished.play().volume = settings["finished"]["volume"]

            # Print winner name
            self.winner_label = pyglet.text.Label(winner["name"],
                font_name=settings["wheel"]["font"], font_size=64, 
                width=900, multiline=True, x=500, y=500, 
                color=get_text_color(winner["color"]),
                anchor_x='center', anchor_y='center', align='center',
                group=self.winner_group, batch=self.batch)

            self.winner_bg = pyglet.shapes.Rectangle(
                x=500-(self.winner_label.content_width//2)-25,
                y=500-(self.winner_label.content_height//2)-25,
                width=self.winner_label.content_width+50,
                height=self.winner_label.content_height+50,
                color=winner["color"],
                group=self.background_group, batch=self.batch)

            if winner["sub"]:
                self.sub = pyglet.text.Label(winner["sub"],
                    font_name=settings["wheel"]["font"], font_size=32,
                    width=900, multiline=True,
                    x=500, y=500-(self.winner_label.content_height//2)-25,
                    color=get_text_color(winner["color"]),
                    anchor_x='center', anchor_y='top', align='center',
                    group=self.winner_group, batch=self.batch)

                if self.sub.content_width > self.winner_label.content_width:
                    self.winner_bg.width = self.sub.content_width+50
                    self.winner_bg.x=500-(self.sub.content_width//2)-25

                self.winner_bg.height += self.sub.content_height + 25
                self.winner_bg.y = 500-((self.winner_label.content_height+self.sub.content_height)//2)-50
                self.winner_label.y += (self.sub.content_height//2)
                self.sub.y += (self.sub.content_height//2)



    def on_draw(self):
        self.clear()

        if self.wheel.spinning:
            # If new wedge at pointer, play sound
            old_name = self.wheel.selected["name"]
            self.wheel.rotate(self.velocity)
            if old_name != self.wheel.selected["name"]:
                # Play sound if there isn't one, stopped or has been 33ms
                if not self.player:
                    self.player = self.sound.play()
                    self.player.volume = settings["tick"]["volume"]
                elif self.player.time >= 1/30 or not self.player.playing:
                    self.player = self.sound.play()
                    self.player.volume = settings["tick"]["volume"]

            if self.velocity < 0.003:
                self.velocity -= 0.003
            else:
                self.velocity -= self.velocity * (
                    (settings["wheel"]["decel_rate"]) / 100)

            if self.velocity < 0:
                self.wheel.spinning = False

                self.handle_win(self.wheel.selected)

                # Delete trigger files to mitigate accidental presses
                if pathlib.Path(path.join(w_dir, "spin")).is_file():
                    os.remove(path.join(w_dir, "spin"))
                if pathlib.Path(path.join(w_dir, "import")).is_file():
                    os.remove(path.join(w_dir, "import"))
        else:
            if self.wheel.idle:
                # Ambient rotating
                self.wheel.rotate(0.02)

            if pathlib.Path(path.join(w_dir, "import")).is_file():
                # Clear winner on re-import
                if self.winner_label:
                    self.winner_label = None
                    self.winner_bg = None
                    if self.sub:
                        self.sub = None

                self.wheel = None
                self.wheel = Wheel(self.center_sprite, self.batch)
                os.remove(path.join(w_dir, "import"))

            elif pathlib.Path(path.join(w_dir, "spin")).is_file():
                # Clear winner on re-spin
                if self.winner_label:
                    self.winner_label = None
                    self.winner_bg = None
                    if self.sub:
                        self.sub = None      

                self.wheel.spinning = True
                self.wheel.idle = False
                # Random spin duration
                self.velocity = self.initial_velocity + randint(25,100)
                os.remove(path.join(w_dir, "spin"))       

        #self.fps_display.draw()
        self.batch.draw()


if pathlib.Path(path.join(w_dir, "spin")).is_file():
    os.remove(path.join(w_dir, "spin"))
if pathlib.Path(path.join(w_dir, "import")).is_file():
    os.remove(path.join(w_dir, "import"))

config = pyglet.gl.Config()
config.sample_buffers = 1
config.samples = 8
window = Sorcle(config)

pyglet.app.run()