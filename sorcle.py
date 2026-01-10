import pyglet
import requests
import csv
import pathlib
import sys, os
from os import path
from io import StringIO
from random import choice, randint

if getattr(sys, 'frozen', False):
    w_dir = pathlib.Path(sys._MEIPASS).parent
else:
    w_dir = os.path.dirname(os.path.abspath(__file__))
pyglet.resource.path = [str(w_dir)]

import tomllib
with open(path.join(w_dir, "settings.toml"), "rb") as f:
    settings = tomllib.load(f)

def get_text_color(color):
    color_intensity = (color[0]*.299 + color[1]*.587 + color[2]*.114)
    if color_intensity > 149:
        return (2, 2, 2)
    else:
        return (255, 255, 255)

class Wedge(pyglet.shapes.Sector):

    def __init__(self, name, start_angle, angle, color, 
        wedge_group, text_group, batch):
        super().__init__(x = 500, y = 500, radius=495,
            start_angle = start_angle, angle = angle, color = color,
            group = wedge_group, batch=batch)

        self.name = name

        # Trim name if too long
        if len(name) > 24:
            disp_name = name[:22] + "..."
        else:
            disp_name = name

        font_size = int(angle*.66) + 12
        if font_size > 24:
            font_size = 24

        self.label = pyglet.text.Label(
            text=disp_name, font_name=settings["wheel"]["font"], x=500, y=500, 
            font_size=font_size, color=get_text_color(color), width=485,
            align='right', anchor_y='center', group=text_group, batch=batch,
            rotation=(-(start_angle+(start_angle+angle))/2-.1))

    def rotate(self, velocity):
        self.start_angle = (self.start_angle + velocity) % 360
        self.label.rotation = (self.label.rotation - velocity) % 360

        return (self.start_angle + self.angle) % 360 < self.start_angle

class Wheel:

    wedges = []
    spinning = False
    finished = False
    idle = True
    selected = {"name": "", "color": (0,0,0,0)}
    
    def __init__(self, wedge_group, text_group, sprite_group, batch):
        self.batch = batch
        self.wedge_group = wedge_group
        self.text_group = text_group

        self.colors = []
        for color in settings["wheel"]["colors"]:
            self.colors.append(tuple(color))

        # Set anchor for center image 
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
            x=500, y=500, group=sprite_group, batch=batch)
        self.center_sprite.update(scale=settings["center"]["scale"])

        self.import_spreadsheet()

    def import_spreadsheet(self):
        self.wedges = []

        # Downlaod spreadsheet from Google; id=document, gid=specific sheet
        # gid on a single sheet document will often be 0
        params = {
            "gid": settings["spreadsheet"]["gid"],
            "format": "tsv"
        }
        r = requests.get(("https://docs.google.com/spreadsheets/d/"
            f"{settings['spreadsheet']['id']}/export"), params=params)
        sheet = csv.reader(StringIO(r.text, newline="\n"), delimiter="\t")
        
        # Iterate to starting row
        for i in range(settings["spreadsheet"]["row"]-1):
            next(sheet)

        # Because csv.reader gets consumed when used, need temp list for count
        temp_wedges = []
        for row in sheet:
            game_name = row[settings["spreadsheet"]["title_column"]-1]
            # Filter out dupe games if setting is true
            if settings["wheel"]["remove_dupes"]:
                if game_name and (game_name not in temp_wedges):
                    temp_wedges.append(game_name)
            # Otherwise, put the dupes next to each other to combine later
            else:
                if game_name and (game_name in temp_wedges):
                    temp_wedges.insert(temp_wedges.index(game_name), game_name)
                elif game_name:
                    temp_wedges.append(game_name)

        # Calculate angle for wedges
        wedge_num = len(temp_wedges)
        angle_per_wedge = 360 / wedge_num

        curr_angle = -90.0
        curr_wedge = 0
        prev_color = (0,0,0)
        for wedge in temp_wedges:

            dupe_wedge = False
            if not settings["wheel"]["remove_dupes"]:
                if curr_wedge > 0:
                    if wedge == self.wedges[-1].name:
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
                    valid_colors.remove(self.wedges[0].color[:-1])
                color = choice(valid_colors)
                prev_color = color

                self.wedges.append(Wedge(name=wedge, start_angle=curr_angle,
                    angle=angle_per_wedge, color=color, batch=self.batch,
                    wedge_group=self.wedge_group, text_group=self.text_group))

            curr_angle += angle_per_wedge
            curr_wedge += 1

    def rotate(self, velocity):
        if settings["center"]["rotate"]:
            self.center_sprite.rotation = (
                self.center_sprite.rotation - velocity) % 360

        for wedge in self.wedges:
            is_selected = wedge.rotate(velocity)
            if self.spinning and is_selected:
                if self.selected["name"] != wedge.name:
                    self.selected["name"] = wedge.name
                    self.selected["color"] = wedge.color[:-1]


class Sorcle(pyglet.window.Window):

    initial_velocity = 25

    def __init__(self, config):
        super().__init__(width = 1200, height = 1000, caption = "Sorcle",
            config = config, style='transparent')

        # For crisp pixel scaling
        if settings["window"]["nearest_neighbour"]:
            pyglet.image.Texture.default_mag_filter = pyglet.gl.GL_NEAREST
            pyglet.image.Texture.default_min_filter = pyglet.gl.GL_NEAREST

        #self.fps_display = pyglet.window.FPSDisplay(self)
        self.batch = pyglet.graphics.Batch()
        self.wedge_group = pyglet.graphics.Group(order=-1)
        self.text_group = pyglet.graphics.Group(order=2)
        self.sprite_group = pyglet.graphics.Group(order=3)

        self.wheel = Wheel(self.wedge_group, self.text_group,
            self.sprite_group, self.batch)

        # Position pointer, change anchor keeping centered regardless of size
        pyglet.resource.path = [w_dir]
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
            path.join(w_dir, 'ping.wav'), streaming=False)
        self.player = None

        self.winner_group = pyglet.graphics.Group(order=5)
        self.winner = None
        self.background_group = pyglet.graphics.Group(order=4)
        self.winner_bg = None


    def on_draw(self):
        pyglet.gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        self.clear()

        if self.wheel.spinning:
            # If new wedge at pointer, play sound
            old_name = self.wheel.selected["name"]
            self.wheel.rotate(self.velocity)
            if old_name != self.wheel.selected["name"]:
                # Play sound if there isn't one, stopped or has been 33ms
                if not self.player:
                    self.player = self.sound.play()
                elif self.player.time > 0.033 or not self.player.playing:
                    self.player = self.sound.play()

            # Approx velocity deceleration; this sucks but it works
            if self.velocity > 50:
                self.velocity -= 1.0
            if self.velocity > 25:
                self.velocity -= 0.5
            elif self.velocity > 10:
                self.velocity -= 0.1
            elif self.velocity > 5:
                self.velocity -= 0.05
            elif self.velocity > 3:
                self.velocity -= 0.02
            elif self.velocity > 1:
                self.velocity -= 0.01
            elif self.velocity > 0.5:
                self.velocity -= 0.005
            elif self.velocity > 0.05:
                self.velocity -= 0.0005
            elif 0 < self.velocity < 0.05:
                self.velocity -= 0.0002

            if self.velocity < 0:
                self.wheel.spinning = False

                # Silently print to file
                with open(path.join(w_dir, "winner.txt"), 'w') as f:
                    f.write(self.wheel.selected_name)
                
                if not settings["wheel"]["suppress_win"]:
                    finished = pyglet.media.load(
                        path.join(w_dir, 'finished.wav')).play()

                    # Print winner name
                    self.winner = pyglet.text.Label(self.wheel.selected["name"],
                        font_name=settings["wheel"]["font"], font_size=64, 
                        width=900, multiline=True, x=500, y=500, 
                        color=get_text_color(self.wheel.selected["color"]),
                        anchor_x='center', anchor_y='center', align='center',
                        group=self.winner_group, batch=self.batch)

                    self.winner_bg = pyglet.shapes.Rectangle(
                        x=500-(self.winner.content_width/2)-25,
                        y=500-(self.winner.content_height/2)-25,
                        width=self.winner.content_width+50,
                        height=self.winner.content_height+50,
                        color=self.wheel.selected["color"],
                        group=self.background_group, batch=self.batch)

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
                if self.winner:
                    self.winner = None
                    self.winner_bg = None

                self.wheel = None
                self.wheel = Wheel(self.wedge_group, self.text_group,
                    self.sprite_group, self.batch)
                os.remove(path.join(w_dir, "import"))

            elif pathlib.Path(path.join(w_dir, "spin")).is_file():

                # Clear winner on re-spin
                if self.winner:
                    self.winner = None
                    self.winner_bg = None      

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