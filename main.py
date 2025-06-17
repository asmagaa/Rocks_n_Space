from textual.app import App, ComposeResult
from textual.widgets import Static, Button
from textual.containers import Vertical
from textual.events import Key
from textual.timer import Timer
from rich.text import Text
import random

MAP_WIDTH = 20 + 1
MAP_HEIGHT = 20 + 1

class Rock:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy

    def move(self):
        self.x += self.dx
        self.y += self.dy

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move(self, dx, dy, map_width, map_height):
        new_x = self.x + dx
        new_y = self.y + dy
        if 0 <= new_x < map_width and 0 <= new_y < map_height:
            self.x = new_x
            self.y = new_y
            return True
        return False

class GameMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [['.' for _ in range(width)] for _ in range(height)]

class GameWidget(Static):
    def __init__(self):
        super().__init__()
        self.game_map = GameMap(MAP_WIDTH, MAP_HEIGHT)
        self.player = Player(MAP_WIDTH // 2, MAP_HEIGHT // 2)
        self.rocks = []
        self.game_over = False
        self.survival_time = 0

    def spawn_rock(self):
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            x, y, dx, dy = random.randint(0, MAP_WIDTH-1), 0, 0, 1
        elif side == 'bottom':
            x, y, dx, dy = random.randint(0, MAP_WIDTH-1), MAP_HEIGHT-1, 0, -1
        elif side == 'left':
            x, y, dx, dy = 0, random.randint(0, MAP_HEIGHT-1), 1, 0
        else:
            x, y, dx, dy = MAP_WIDTH-1, random.randint(0, MAP_HEIGHT-1), -1, 0
        self.rocks.append(Rock(x, y, dx, dy))

    def move_rocks(self):
        for rock in self.rocks:
            rock.move()
        self.rocks = [
            rock for rock in self.rocks
            if 0 <= rock.x < MAP_WIDTH and 0 <= rock.y < MAP_HEIGHT
        ]

    def check_collision(self):
        for rock in self.rocks:
            if rock.x == self.player.x and rock.y == self.player.y:
                self.game_over = True

    def render(self) -> Text:
        if self.game_over:
            return Text(
                f"\n\nYOU LOSE\n\nSurvival Time: {self.survival_time:.1f} seconds\n\nPress R to retry or Q to quit.",
                justify="center")

        minutes = int(self.survival_time // 60)
        seconds = int(self.survival_time % 60)
        time_display = f"Time: {minutes:02d}:{seconds:02d}"

        display = []
        for y in range(self.game_map.height):
            line = ""
            for x in range(self.game_map.width):
                if x == self.player.x and y == self.player.y:
                    line += "O"
                elif any(rock.x == x and rock.y == y for rock in self.rocks):
                    line += "x"
                else:
                    line += "_"
            display.append(line)
        return Text(time_display + "\n\n" + "\n".join(display), justify="center")

class MenuWidget(Vertical):
    def compose(self) -> ComposeResult:
        yield Button("Play", id="play")
        yield Button("Options", id="options")
        yield Button("Leave", id="leave")

class GameApp(App):
    CSS_PATH = "styles.tcss"

    def __init__(self):
        super().__init__()
        self.state = "menu"
        self.game_widget = None
        self.menu_widget = None
        self.rock_timer: Timer | None = None
        self.time_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        if self.state == "menu":
            self.menu_widget = MenuWidget()
            yield self.menu_widget
        else:
            self.game_widget = GameWidget()
            yield self.game_widget

    def on_mount(self):
        if self.state == "game":
            self.rock_timer = self.set_interval(0.5, self.update_rocks)
            self.time_timer = self.set_interval(0.5, self.update_time)

    def update_rocks(self):
        if self.game_widget and not self.game_widget.game_over:
            self.game_widget.spawn_rock()
            self.game_widget.move_rocks()
            self.game_widget.check_collision()
            self.game_widget.refresh()

    def update_time(self):
        if self.game_widget and not self.game_widget.game_over:
            self.game_widget.survival_time += 0.5
            self.game_widget.refresh()

    def on_button_pressed(self, event):
        if event.button.id == "play":
            self.state = "game"
            if self.menu_widget:
                self.menu_widget.remove()
            if self.game_widget:
                self.game_widget.remove()
            self.game_widget = GameWidget()
            self.mount(self.game_widget)
            self.rock_timer = self.set_interval(0.5, self.update_rocks)
            self.time_timer = self.set_interval(0.5, self.update_time)
        elif event.button.id == "leave":
            self.exit()

    def on_key(self, event: Key) -> None:
        if self.state == "menu":
            return
        if self.game_widget and self.game_widget.game_over:
            if event.key.lower() == "q":
                self.exit()
            if event.key.lower() == "r":
                self.game_widget.remove()
                self.game_widget = GameWidget()
                self.mount(self.game_widget)
                if self.rock_timer:
                    self.rock_timer.stop()
                if self.rock_timer:
                    self.time_timer.stop()
                self.rock_timer = self.set_interval(0.5, self.update_rocks)
                self.time_timer = self.set_interval(0.5, self.update_time)
            return
        key = event.key.lower()
        moved = False
        if key == "q":
            self.exit()
            return
        if key == "w":
            moved = self.game_widget.player.move(0, -1, MAP_WIDTH, MAP_HEIGHT)
        elif key == "s":
            moved = self.game_widget.player.move(0, 1, MAP_WIDTH, MAP_HEIGHT)
        elif key == "a":
            moved = self.game_widget.player.move(-1, 0, MAP_WIDTH, MAP_HEIGHT)
        elif key == "d":
            moved = self.game_widget.player.move(1, 0, MAP_WIDTH, MAP_HEIGHT)
        if moved:
            self.game_widget.check_collision()
            self.game_widget.refresh()

def main():
    app = GameApp()
    app.run()

if __name__ == "__main__":
    main()