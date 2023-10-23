from os.path import join
from random import choice
from sys import exit

from settings import *
from timer import Timer


class Game:
    def __init__(self, get_next_shape, update_score):
        # general
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.display_surface = pygame.display.get_surface()

        self.rect = self.surface.get_rect(topleft=(PADDING, PADDING))
        self.sprite_group = pygame.sprite.Group()

        # game connection
        self.get_next_shape = get_next_shape
        self.update_score = update_score

        # lines for the grid
        self.line_surface = self.surface.copy()
        self.line_surface.fill((0, 255, 0))
        self.line_surface.set_colorkey((0, 255, 0))
        self.line_surface.set_alpha(120)

        # test
        # self.block = Block(self.sprite_group,pygame.Vector2(3,5),'red')

        # tetromino
        self.field_data = [[0 for x in range(COLUMNS)] for y in range(ROWS)]

        self.tetromino = Tetromino(
            choice(list(TETROMINOS.keys())),
            self.sprite_group,
            self.create_new_tetromino,
            self.field_data,
        )

        # timer
        self.down_speed = UPDATE_START_SPEED
        self.down_speed_faster = self.down_speed * 0.3
        self.down_pressed = False
        self.timers = {
            "vertical_move": Timer(self.down_speed, True, self.move_down),
            "horizontal_move": Timer(MOVE_WAIT_TIME),
            "rotate": Timer(ROTATE_WAIT_TIME),
        }
        self.timers["vertical_move"].activate()

        # score
        self.current_level = 1
        self.current_score = 0
        self.current_lines = 0

        # audio
        self.landing_sound = pygame.mixer.Sound(join("sound", "landing.wav"))
        self.landing_sound.set_volume(0.06)

    def calculate_score(self, num_lines):
        self.current_lines += num_lines
        self.current_score += SCORE_DATA[num_lines] * self.current_level

        # every 10 lines increase the score
        if self.current_level / 10 > self.current_level:
            self.current_level += 1
            self.down_speed *= 0.75
            self.down_speed_faster = self.down_speed * 0.3
            self.timers["vertical_move"].duration = self.down_speed

        self.update_score(self.current_lines, self.current_score, self.current_level)

    def check_game_over(self):
        for block in self.tetromino.blocks:
            if block.pos.y < 0:
                # todo show game over screen and show score
                exit()

    def create_new_tetromino(self):
        self.landing_sound.play()
        self.check_game_over()
        self.check_finished_rows()

        self.tetromino = Tetromino(
            self.get_next_shape(),
            self.sprite_group,
            self.create_new_tetromino,
            self.field_data,
        )

    def timer_update(self):
        for timer in self.timers.values():
            timer.update()

    def move_down(self):
        # print('timer move down')
        self.tetromino.move_down()

    def drawgrid(self):
        for col in range(1, COLUMNS):
            x = col * CELL_SIZE
            pygame.draw.line(
                self.line_surface, LINE_COLOR, (x, 0), (x, self.surface.get_height()), 1
            )
        for row in range(1, ROWS):
            y = row * CELL_SIZE
            pygame.draw.line(
                self.line_surface, LINE_COLOR, (0, y), (self.surface.get_width(), y), 1
            )
        self.surface.blit(self.line_surface, (0, 0))

    def input(self):
        keys = pygame.key.get_pressed()

        # check for the horzontal movement
        if not self.timers["horizontal_move"].active:
            if keys[pygame.K_LEFT]:
                self.tetromino.move_horizontal(-1)
                self.timers["horizontal_move"].activate()
            if keys[pygame.K_RIGHT]:
                self.tetromino.move_horizontal(1)
                self.timers["horizontal_move"].activate()

        # Check for the rotation
        if not self.timers["rotate"].active:
            if keys[pygame.K_UP]:
                self.tetromino.rotate()
                self.timers["rotate"].activate()

        # check for the down speedup
        if not self.down_pressed and keys[pygame.K_DOWN]:
            self.down_pressed = True
            # print('down pressed')
            self.timers["vertical_move"].duration = self.down_speed_faster

        if self.down_pressed and not keys[pygame.K_DOWN]:
            self.down_pressed = False
            # print('down released')
            self.timers["vertical_move"].duration = self.down_speed

    def check_finished_rows(self):
        # get the full row indexes
        delete_rows = []
        for i, row in enumerate(self.field_data):
            if all(row):
                delete_rows.append(i)

        if delete_rows:
            for delete_row in delete_rows:
                # delete the full rows
                for block in self.field_data[delete_row]:
                    block.kill()

                # move the blocks down
                for row in self.field_data:
                    for block in row:
                        if block and block.pos.y < delete_row:
                            block.pos.y += 1
            # rebuild field.data
            self.field_data = [[0 for x in range(COLUMNS)] for y in range(ROWS)]
            for block in self.sprite_group:
                self.field_data[int(block.pos.y)][int(block.pos.x)] = block

            # check score
            self.calculate_score(len(delete_rows))

    def run(self):
        # update
        self.input()
        self.timer_update()
        self.sprite_group.update()

        # draw grid
        self.surface.fill("gray")
        self.sprite_group.draw(self.surface)

        self.drawgrid()
        self.display_surface.blit(self.surface, (PADDING, PADDING))
        pygame.draw.rect(self.display_surface, LINE_COLOR, self.rect, 2, 2)


class Tetromino:
    def __init__(self, shape1, group1, create_new_tetromino, field_data):
        # setup
        self.shape = shape1
        self.block_positions = TETROMINOS[shape1]["shape"]
        self.color = TETROMINOS[shape1]["color"]
        self.create_new_tetromino = create_new_tetromino
        self.field_data = field_data

        # create block
        self.blocks = [Block(group1, pos, self.color) for pos in self.block_positions]

    def next_move_horizontal_collide(self, blocks, amount):
        collision_list = [
            block.horizontal_collide(int(block.pos.x + amount), self.field_data)
            for block in self.blocks
        ]
        # print(f"HORIZONTAL collide {collision_list}")
        return True if any(collision_list) else False

    def next_move_vertical_collide(self, blocks, amount):
        collision_list = [
            block.vertical_collide(int(block.pos.y + amount), self.field_data)
            for block in self.blocks
        ]
        # print(f"vertical collide {collision_list}")
        return True if any(collision_list) else False

    def move_horizontal(self, amount):
        if not self.next_move_horizontal_collide(self.blocks, amount):
            for block in self.blocks:
                block.pos.x += amount

    # movement
    def move_down(self):
        if not self.next_move_vertical_collide(self.blocks, 1):
            for block in self.blocks:
                block.pos.y += 1
        else:
            for block in self.blocks:
                self.field_data[int(block.pos.y)][int(block.pos.x)] = block
            self.create_new_tetromino()

    def rotate(self):
        if self.shape != "O":
            # 1 Pivot point
            pivot_pos = self.blocks[0].pos

            # 2 new block positions
            new_block_positions = [block.rotate(pivot_pos) for block in self.blocks]

            # 3 collision check
            for pos in new_block_positions:
                # horzontal check
                print(pos.x, pos.y)
                if pos.x < 0 or pos.x >= COLUMNS:
                    return

                # field check -> collision with other pieces
                if self.field_data[int(pos.y)][int(pos.x)]:
                    return

                # vertival check / Floor check
                if pos.y < 0 or pos.y > ROWS:
                    return

            # 4 Implement nre positions
            for i, block in enumerate(self.blocks):
                block.pos = new_block_positions[i]


class Block(pygame.sprite.Sprite):
    def __init__(self, group, pos, color):
        super().__init__(group)
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))
        # pos=(0,0)
        # color='red'
        self.image.fill(color)
        # position
        self.pos = pygame.Vector2(pos) + BLOCK_OFFSET
        x = self.pos.x * CELL_SIZE
        y = self.pos.y * CELL_SIZE
        # place the image into the desired rectangle
        self.rect = self.image.get_rect(topleft=(x, y))

    def rotate(self, pivot_pos):
        # distance = self.pos - pivot_pos
        # rotated = distance.rotate(90)
        # new_pos = pivot_pos + rotated
        # return new_pos
        return pivot_pos + (self.pos - pivot_pos).rotate(90)

    def horizontal_collide(self, x, field_data):
        if not 0 <= x < COLUMNS:
            return True
        if field_data[int(self.pos.y)][x]:
            return True

    def vertical_collide(self, y, field_data):
        if y >= ROWS:
            return True
        if y >= 0 and field_data[y][int(self.pos.x)]:
            return True

    def update(self):
        # place the image into the same rectangle
        # self.rect = self.image.get_rect (topleft=self.pos *CELL_SIZE)  #this one also works
        self.rect.topleft = self.pos * CELL_SIZE
        # print(self.pos)
