import pygame
import random
import math

# Инициализация Pygame
pygame.init()

# Получаем размер экрана
infoObject = pygame.display.Info()
SCREEN_WIDTH = infoObject.current_w
SCREEN_HEIGHT = infoObject.current_h

# Константы
BLOCK_SIZE = 30  # Размер одного блока
GRID_WIDTH = 12  # Ширина игрового поля в блоках
GRID_HEIGHT = 22  # Высота игрового поля в блоках

# Вычисляем отступ слева для центрирования игрового поля
GRID_LEFT_MARGIN = (SCREEN_WIDTH - (GRID_WIDTH * BLOCK_SIZE + 300)) // 2  # 300px для интерфейса справа

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
CYAN = (0, 240, 240)  # Более яркий циан
YELLOW = (240, 240, 0)  # Более яркий желтый
MAGENTA = (240, 0, 240)  # Более яркая пурпурная
RED = (240, 0, 0)  # Более яркий красный
GREEN = (0, 240, 0)  # Более яркий зеленый
BLUE = (0, 0, 240)  # Более яркий синий
ORANGE = (240, 160, 0)  # Более яркий оранжевый

COLORS = [CYAN, YELLOW, MAGENTA, RED, GREEN, BLUE, ORANGE]

# Фигуры тетрамино
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]]   # Z
]

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.SysFont('Arial', 14)

    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)

class Animation:
    def __init__(self, duration):
        self.duration = duration
        self.start_time = 0
        self.is_playing = False

    def start(self):
        self.start_time = pygame.time.get_ticks()
        self.is_playing = True

    def update(self):
        if not self.is_playing:
            return 1.0
        current_time = pygame.time.get_ticks()
        progress = (current_time - self.start_time) / self.duration
        if progress >= 1.0:
            self.is_playing = False
            return 1.0
        return progress

class Statistics:
    def __init__(self):
        self.total_lines = 0
        self.total_score = 0
        self.max_level = 1
        self.games_played = 0
        self.best_score = 0
        self.achievements = {
            'first_line': {'name': 'Первая линия', 'achieved': False},
            'level_5': {'name': 'Уровень 5', 'achieved': False},
            'score_1000': {'name': 'Счет 1000', 'achieved': False},
            'score_5000': {'name': 'Счет 5000', 'achieved': False},
            'lines_50': {'name': '50 линий', 'achieved': False}
        }

    def update(self, lines, score, level):
        self.total_lines += lines
        self.total_score += score
        self.max_level = max(self.max_level, level)
        self.best_score = max(self.best_score, score)
        
        # Проверка достижений
        if lines > 0 and not self.achievements['first_line']['achieved']:
            self.achievements['first_line']['achieved'] = True
        if level >= 5 and not self.achievements['level_5']['achieved']:
            self.achievements['level_5']['achieved'] = True
        if score >= 1000 and not self.achievements['score_1000']['achieved']:
            self.achievements['score_1000']['achieved'] = True
        if score >= 5000 and not self.achievements['score_5000']['achieved']:
            self.achievements['score_5000']['achieved'] = True
        if self.total_lines >= 50 and not self.achievements['lines_50']['achieved']:
            self.achievements['lines_50']['achieved'] = True

class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption('Тетрис')
        self.clock = pygame.time.Clock()
        self.statistics = Statistics()
        self.animations = {
            'line_clear': Animation(500),  # 500ms для анимации очистки линии
            'piece_lock': Animation(200),  # 200ms для анимации фиксации фигуры
        }
        self.buttons = {
            'restart': Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 100, 200, 50, 
                            "Начать заново", (50, 50, 60), (70, 70, 80)),
            'exit': Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 160, 200, 50,
                          "Выход", (50, 50, 60), (70, 70, 80))
        }
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0
        try:
            self.font = pygame.font.SysFont('Comic Sans MS', 36)
            self.small_font = pygame.font.SysFont('Comic Sans MS', 24)
        except:
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
        self.move_left = False
        self.move_right = False
        self.move_down = False
        self.move_delay = 100
        self.move_time_left = 0
        self.move_time_right = 0
        self.move_time_down = 0
        self.show_statistics = False
        self.lines_to_clear = []  # Список линий для анимации очистки

    def new_piece(self):
        # Создание новой фигуры
        shape = random.choice(SHAPES)
        color = random.choice(COLORS)
        return {
            'shape': shape,
            'color': color,
            'x': GRID_WIDTH // 2 - len(shape[0]) // 2,
            'y': 0
        }

    def valid_move(self, piece, x, y):
        # Проверка возможности движения
        for i in range(len(piece['shape'])):
            for j in range(len(piece['shape'][0])):
                if piece['shape'][i][j]:
                    new_x = x + j
                    new_y = y + i
                    if new_x < 0 or new_x >= GRID_WIDTH or new_y >= GRID_HEIGHT:
                        return False
                    if new_y >= 0 and self.grid[new_y][new_x]:
                        return False
        return True

    def merge_piece(self):
        # Добавление фигуры в сетку
        for i in range(len(self.current_piece['shape'])):
            for j in range(len(self.current_piece['shape'][0])):
                if self.current_piece['shape'][i][j]:
                    self.grid[self.current_piece['y'] + i][self.current_piece['x'] + j] = self.current_piece['color']

    def remove_complete_lines(self):
        lines_cleared = 0
        i = GRID_HEIGHT - 1
        
        # Находим и удаляем заполненные линии
        while i >= 0:
            if all(self.grid[i]):
                # Удаляем заполненную линию
                del self.grid[i]
                # Добавляем новую пустую линию сверху
                self.grid.insert(0, [0 for _ in range(GRID_WIDTH)])
                lines_cleared += 1
            else:
                i -= 1
        
        if lines_cleared > 0:
            self.statistics.update(lines_cleared, self.score, self.level)
        
        return lines_cleared

    def rotate_piece(self):
        # Поворот фигуры
        shape = self.current_piece['shape']
        rotated = list(zip(*shape[::-1]))
        if self.valid_move({'shape': rotated, 'x': self.current_piece['x'], 'y': self.current_piece['y']},
                          self.current_piece['x'], self.current_piece['y']):
            self.current_piece['shape'] = rotated

    def reset_game(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0

    def calculate_level(self):
        # Повышаем уровень каждые 10 линий
        self.level = (self.lines_cleared_total // 10) + 1
        return max(50, 250 - (self.level - 1) * 20)  # Уменьшаем задержку падения с каждым уровнем

    def drop_piece(self):
        # Мгновенный сброс фигуры вниз
        drop_distance = 0
        while self.valid_move(self.current_piece, self.current_piece['x'], self.current_piece['y'] + 1):
            self.current_piece['y'] += 1
            drop_distance += 1
        return drop_distance

    def draw_shadow(self, piece, color):
        """Отрисовка тени для падающей фигуры"""
        shadow_y = piece['y']
        # Находим позицию, где фигура остановится
        while self.valid_move(piece, piece['x'], shadow_y + 1):
            shadow_y += 1
        
        # Рисуем полупрозрачную тень
        for i in range(len(piece['shape'])):
            for j in range(len(piece['shape'][0])):
                if piece['shape'][i][j]:
                    shadow_color = (color[0]//3, color[1]//3, color[2]//3)
                    pygame.draw.rect(self.screen, shadow_color,
                                   (GRID_LEFT_MARGIN + (piece['x'] + j) * BLOCK_SIZE,
                                    (shadow_y + i) * BLOCK_SIZE,
                                    BLOCK_SIZE - 1, BLOCK_SIZE - 1))

    def draw_block(self, x, y, color):
        """Отрисовка блока с эффектом объема и свечения"""
        # Основной блок
        pygame.draw.rect(self.screen, color,
                        (x, y, BLOCK_SIZE - 1, BLOCK_SIZE - 1))
        
        # Эффект свечения
        glow_surface = pygame.Surface((BLOCK_SIZE * 2, BLOCK_SIZE * 2), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (*color, 30),
                        (BLOCK_SIZE//2, BLOCK_SIZE//2, BLOCK_SIZE, BLOCK_SIZE))
        self.screen.blit(glow_surface, (x - BLOCK_SIZE//2, y - BLOCK_SIZE//2))
        
        # Светлая грань (сверху и слева)
        light_color = (min(color[0] + 50, 255),
                      min(color[1] + 50, 255),
                      min(color[2] + 50, 255))
        pygame.draw.line(self.screen, light_color,
                        (x, y), (x + BLOCK_SIZE - 1, y))
        pygame.draw.line(self.screen, light_color,
                        (x, y), (x, y + BLOCK_SIZE - 1))
        
        # Темная грань (снизу и справа)
        dark_color = (max(color[0] - 50, 0),
                     max(color[1] - 50, 0),
                     max(color[2] - 50, 0))
        pygame.draw.line(self.screen, dark_color,
                        (x + BLOCK_SIZE - 1, y),
                        (x + BLOCK_SIZE - 1, y + BLOCK_SIZE - 1))
        pygame.draw.line(self.screen, dark_color,
                        (x, y + BLOCK_SIZE - 1),
                        (x + BLOCK_SIZE - 1, y + BLOCK_SIZE - 1))

    def draw_background(self):
        """Улучшенный фон с градиентом и узором"""
        # Создаем градиентный фон
        for i in range(SCREEN_HEIGHT):
            # Вычисляем значения цветовых компонентов
            blue = int((i / SCREEN_HEIGHT) * 40)
            color = (0, 0, blue + 10)
            pygame.draw.line(self.screen, color, (0, i), (SCREEN_WIDTH, i))

    def draw(self):
        self.draw_background()  # Рисуем фон
        
        # Отрисовка бокового меню
        interface_x = GRID_LEFT_MARGIN + GRID_WIDTH * BLOCK_SIZE + 40
        menu_width = 260

        def draw_section(y, height, title=None):
            s = pygame.Surface((menu_width, height))
            s.fill((30, 30, 40))
            s.set_alpha(200)
            self.screen.blit(s, (interface_x, y))
            
            # Добавляем градиентную рамку
            gradient_colors = [(50, 50, 60), (70, 70, 80)]
            for i, color in enumerate(gradient_colors):
                pygame.draw.rect(self.screen, color,
                               (interface_x - i, y - i,
                                menu_width + i * 2, height + i * 2), 1)
            
            if title:
                # Добавляем подчеркивание для заголовка
                title_text = self.font.render(title, True, WHITE)
                self.screen.blit(title_text, (interface_x + 10, y + 10))
                pygame.draw.line(self.screen, WHITE,
                               (interface_x + 10, y + 45),
                               (interface_x + menu_width - 10, y + 45))
                return y + 50
            return y

        # Отрисовка границ игрового поля
        pygame.draw.rect(self.screen, (50, 50, 60),
                        (GRID_LEFT_MARGIN - 2, 0,
                         GRID_WIDTH * BLOCK_SIZE + 4,
                         GRID_HEIGHT * BLOCK_SIZE + 2), 2)

        # Отрисовка сетки и блоков
        for i in range(GRID_HEIGHT):
            for j in range(GRID_WIDTH):
                # Отрисовка сетки более тонкими линиями
                pygame.draw.rect(self.screen, (40, 40, 50),
                               (GRID_LEFT_MARGIN + j * BLOCK_SIZE,
                                i * BLOCK_SIZE,
                                BLOCK_SIZE, BLOCK_SIZE), 1)
                if self.grid[i][j]:
                    self.draw_block(GRID_LEFT_MARGIN + j * BLOCK_SIZE,
                                  i * BLOCK_SIZE,
                                  self.grid[i][j])

        # Отрисовка текущей фигуры с плавным движением
        if self.current_piece:
            # Отрисовка тени
            self.draw_shadow(self.current_piece, self.current_piece['color'])
            
            for i in range(len(self.current_piece['shape'])):
                for j in range(len(self.current_piece['shape'][0])):
                    if self.current_piece['shape'][i][j]:
                        # Плавное движение фигуры
                        target_x = GRID_LEFT_MARGIN + (self.current_piece['x'] + j) * BLOCK_SIZE
                        target_y = (self.current_piece['y'] + i) * BLOCK_SIZE
                        self.draw_block(target_x, target_y, self.current_piece['color'])

        # Секция статистики
        stats_y = 20
        stats_height = 180
        content_y = draw_section(stats_y, stats_height, "Статистика")
        
        stats_texts = [
            f'Счет: {self.score}',
            f'Уровень: {self.level}',
            f'Линий: {self.lines_cleared_total}',
            f'Рекорд: {self.statistics.best_score}'
        ]
        
        for i, text in enumerate(stats_texts):
            text_surface = self.font.render(text, True, WHITE)
            self.screen.blit(text_surface, (interface_x + 10, content_y + i * 30))

        # Секция следующей фигуры
        next_y = stats_y + stats_height + 40  # Увеличен отступ между секциями
        next_height = 140
        content_y = draw_section(next_y, next_height, "Следующая фигура")
        
        # Центрируем следующую фигуру
        next_shape = self.next_piece['shape']
        shape_width = len(next_shape[0]) * BLOCK_SIZE
        shape_height = len(next_shape) * BLOCK_SIZE
        next_x = interface_x + (menu_width - shape_width) // 2
        next_piece_y = content_y + (next_height - shape_height - 50) // 2
        
        for i in range(len(next_shape)):
            for j in range(len(next_shape[0])):
                if next_shape[i][j]:
                    self.draw_block(
                        next_x + j * BLOCK_SIZE,
                        next_piece_y + i * BLOCK_SIZE,
                        self.next_piece['color']
                    )

        # Секция достижений
        achievements_y = next_y + next_height + 40  # Увеличен отступ между секциями
        achievements_height = 200
        content_y = draw_section(achievements_y, achievements_height, "Достижения")
        
        for i, (key, achievement) in enumerate(self.statistics.achievements.items()):
            color = GREEN if achievement['achieved'] else GRAY
            text = f"✓ {achievement['name']}" if achievement['achieved'] else f"□ {achievement['name']}"
            text_surface = self.small_font.render(text, True, color)
            self.screen.blit(text_surface, (interface_x + 10, content_y + i * 30))

        # Отрисовка кнопок в игровом меню
        if self.game_over:
            for button in self.buttons.values():
                button.draw(self.screen)

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if self.game_over:
                for name, button in self.buttons.items():
                    if button.handle_event(event):
                        if name == 'restart':
                            self.reset_game()
                            return True
                        elif name == 'exit':
                            return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if not self.game_over:
                    if event.key == pygame.K_LEFT:
                        self.move_left = True
                    elif event.key == pygame.K_RIGHT:
                        self.move_right = True
                    elif event.key == pygame.K_DOWN:
                        self.move_down = True
                    elif event.key == pygame.K_UP:
                        self.rotate_piece()
                    elif event.key == pygame.K_SPACE:
                        drop_distance = self.drop_piece()
                        self.score += drop_distance * 2
            
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    self.move_left = False
                elif event.key == pygame.K_RIGHT:
                    self.move_right = False
                elif event.key == pygame.K_DOWN:
                    self.move_down = False
        
        return True

    def show_start_screen(self):
        """Улучшенный стартовый экран с анимацией и инструкциями"""
        self.screen.fill(BLACK)
        
        # Анимированный заголовок
        title_font = pygame.font.SysFont('Comic Sans MS', 72)
        title_surface = title_font.render('ТЕТРИС', True, WHITE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        
        # Инструкции
        instructions = [
            'ЛЕВО, ПРАВО : Перемещение фигуры',
            'ВВЕРХ : Поворот фигуры',
            'ВНИЗ : Ускорение падения',
            'Пробел : Мгновенное падение'
        ]
        
        instruction_font = pygame.font.SysFont('Comic Sans MS', 24)
        instruction_surfaces = []
        for text in instructions:
            surf = instruction_font.render(text, True, GRAY)
            instruction_surfaces.append(surf)
        
        # Кнопка начала игры
        start_button = Button(
            SCREEN_WIDTH // 2 - 150,
            SCREEN_HEIGHT * 2 // 3,
            300, 60,
            'НАЧАТЬ ИГРУ',
            (50, 50, 60),
            (70, 70, 80)
        )
        
        # Анимационный цикл
        angle = 0
        waiting = True
        clock = pygame.time.Clock()
        
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if start_button.handle_event(event):
                        waiting = False
                if event.type == pygame.MOUSEMOTION:
                    start_button.handle_event(event)
            
            # Очищаем экран и рисуем фон
            self.draw_background()
            
            # Анимация заголовка
            scaled_title = pygame.transform.scale(
                title_surface,
                (int(title_surface.get_width() * (1 + 0.05 * abs(math.sin(angle)))),
                 int(title_surface.get_height() * (1 + 0.05 * abs(math.sin(angle)))))
            )
            scaled_rect = scaled_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
            self.screen.blit(scaled_title, scaled_rect)
            
            # Отрисовка инструкций
            for i, surf in enumerate(instruction_surfaces):
                pos = (SCREEN_WIDTH // 2 - surf.get_width() // 2,
                      SCREEN_HEIGHT // 2 + i * 30)
                self.screen.blit(surf, pos)
            
            # Отрисовка кнопки
            start_button.draw(self.screen)
            
            pygame.display.flip()
            angle += 0.02
            clock.tick(60)

    def run(self):
        self.show_start_screen()  # Показываем экран приветствия
        fall_time = 0
        fall_speed = self.calculate_level()
        
        while True:
            if not self.handle_events():
                return

            if not self.game_over:
                delta_time = self.clock.get_rawtime()
                fall_time += delta_time
                self.clock.tick()

                # Обработка движения
                if self.move_left:
                    self.move_time_left += delta_time
                    if self.move_time_left >= self.move_delay:
                        if self.valid_move(self.current_piece, self.current_piece['x'] - 1, self.current_piece['y']):
                            self.current_piece['x'] -= 1
                        self.move_time_left = 0

                if self.move_right:
                    self.move_time_right += delta_time
                    if self.move_time_right >= self.move_delay:
                        if self.valid_move(self.current_piece, self.current_piece['x'] + 1, self.current_piece['y']):
                            self.current_piece['x'] += 1
                        self.move_time_right = 0

                if self.move_down:
                    self.move_time_down += delta_time
                    if self.move_time_down >= self.move_delay:
                        if self.valid_move(self.current_piece, self.current_piece['x'], self.current_piece['y'] + 1):
                            self.current_piece['y'] += 1
                        self.move_time_down = 0

                if fall_time >= fall_speed:
                    if self.valid_move(self.current_piece, self.current_piece['x'], self.current_piece['y'] + 1):
                        self.current_piece['y'] += 1
                    else:
                        self.merge_piece()
                        lines_cleared = self.remove_complete_lines()
                        self.lines_cleared_total += lines_cleared
                        self.score += lines_cleared * 100 * self.level
                        fall_speed = self.calculate_level()
                        self.current_piece = self.next_piece
                        self.next_piece = self.new_piece()
                        
                        if not self.valid_move(self.current_piece, self.current_piece['x'], self.current_piece['y']):
                            self.game_over = True
                            self.statistics.games_played += 1
                    
                    fall_time = 0

            self.draw()

if __name__ == '__main__':
    game = Tetris()
    game.run()
    pygame.quit() 