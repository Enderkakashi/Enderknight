import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 800
CELL_SIZE = 60
BOARD_OFFSET_X = 50
BOARD_OFFSET_Y = 50
FPS = 60

# Colors
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
BRIGHT_COLORS = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (0,255,255)]
BLACK = (0,0,0)

# Setup screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("BlockBlast Clone")
clock = pygame.time.Clock()

# Load images (placeholders)
background_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
background_img.fill((20,20,30))
block_img = pygame.Surface((CELL_SIZE, CELL_SIZE))
block_img.fill((200,200,200))
white_block_img = pygame.Surface((CELL_SIZE, CELL_SIZE))
white_block_img.fill((255,255,255))
highlight_img = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
highlight_img.fill((255,255,255,100))  # semi-transparent

# Load sounds (placeholders)
pygame.mixer.init()
# pygame.mixer.music.load("background_music.mp3")
# pygame.mixer.music.play(-1)
# clear_sound = pygame.mixer.Sound("clear.wav")

# Board Data
board = [[None for _ in range(9)] for _ in range(9)]  # None = empty

# Pieces Definitions (relative coordinates)
PIECES = [
    [(0,0)],
    [(0,0),(1,0)],
    [(0,0),(0,1)],
    [(0,0),(1,0),(2,0)],
    [(0,0),(0,1),(0,2)],
    [(0,0),(1,0),(0,1)],
    [(0,0),(1,0),(1,1)],
    [(0,0),(0,1),(1,1)],
    [(0,0),(0,1),(0,2),(1,0)],
]

# Piece Tray
current_pieces = []

# Score & streak
score = 0
high_score = 0
streak = 0
streak_timer = 0
combo_texts = []  # {text, pos, tick}

# Particle system placeholder
particles = []  # {x, y, vx, vy, tick}

# White flash cells
white_flash_cells = []  # {x, y, tick}

# Game over
game_over = False

# Selected piece
selected_piece = None
drag_offset = (0,0)

# Restart button
restart_rect = pygame.Rect(SCREEN_WIDTH//2-50, SCREEN_HEIGHT//2+50, 100, 40)

# --- Functions ---

def spawn_pieces():
    global current_pieces
    current_pieces = [random.choice(PIECES) for _ in range(3)]

def draw_board():
    for y in range(9):
        for x in range(9):
            rect = pygame.Rect(BOARD_OFFSET_X + x*CELL_SIZE, BOARD_OFFSET_Y + y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, GRAY, rect, 1)
            if board[y][x]:
                screen.blit(block_img, rect)
    # Draw 3x3 super-square borders
    for sy in range(0,9,3):
        for sx in range(0,9,3):
            rect = pygame.Rect(BOARD_OFFSET_X+sx*CELL_SIZE, BOARD_OFFSET_Y+sy*CELL_SIZE, CELL_SIZE*3, CELL_SIZE*3)
            pygame.draw.rect(screen, WHITE, rect, 2)

def draw_piece(piece, pos, scale=CELL_SIZE):
    x0, y0 = pos
    for dx, dy in piece:
        rect = pygame.Rect(x0 + dx*scale, y0 + dy*scale, scale, scale)
        screen.blit(block_img, rect)

def check_clear():
    global score, white_flash_cells, streak, streak_timer, combo_texts
    cleared = []
    # Rows
    for y in range(9):
        if all(board[y][x] for x in range(9)):
            for x in range(9):
                cleared.append((x,y))
    # Columns
    for x in range(9):
        if all(board[y][x] for y in range(9)):
            for y in range(9):
                cleared.append((x,y))
    # Super-squares
    for sy in range(0,9,3):
        for sx in range(0,9,3):
            if all(board[sy+dy][sx+dx] for dx in range(3) for dy in range(3)):
                for dx in range(3):
                    for dy in range(3):
                        cleared.append((sx+dx, sy+dy))
    # Remove duplicates
    cleared = list(set(cleared))
    if cleared:
        for x,y in cleared:
            white_flash_cells.append({'x':x,'y':y,'tick':0})
        score += 2*len(cleared)
        # combo text
        combo_texts.append({'text':'COMBO!','pos':pygame.mouse.get_pos(),'tick':0})
        # clear_sound.play()
        streak = min(streak+1,3)
        streak_timer = 0
        # Clear board cells after white flash handled separately

def update_white_flash():
    global white_flash_cells, particles
    for cell in white_flash_cells[:]:
        cell['tick'] +=1
        if cell['tick']==15:
            # spawn particles
            particles.append({'x':cell['x'],'y':cell['y'],'tick':0})
        if cell['tick']>=45:
            board[cell['y']][cell['x']] = None
            white_flash_cells.remove(cell)

def update_particles():
    for p in particles[:]:
        p['tick'] +=1
        if p['tick']>30:
            particles.remove(p)

def draw_particles():
    for p in particles:
        rect = pygame.Rect(BOARD_OFFSET_X+p['x']*CELL_SIZE, BOARD_OFFSET_Y+p['y']*CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.circle(screen, random.choice(BRIGHT_COLORS), rect.center, 10)

def draw_white_flash():
    for cell in white_flash_cells:
        rect = pygame.Rect(BOARD_OFFSET_X+cell['x']*CELL_SIZE, BOARD_OFFSET_Y+cell['y']*CELL_SIZE, CELL_SIZE, CELL_SIZE)
        screen.blit(white_block_img, rect)

def draw_score():
    font = pygame.font.SysFont(None,36)
    score_surf = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_surf,(10,10))
    high_surf = font.render(f"High Score: {high_score}", True, WHITE)
    screen.blit(high_surf,(10,50))

def draw_streak_combo():
    font = pygame.font.SysFont(None,36)
    for text in combo_texts[:]:
        text['tick'] +=1
        txt_surf = font.render(text['text'], True, random.choice(BRIGHT_COLORS))
        screen.blit(txt_surf, text['pos'])
        if text['tick']>=60:
            combo_texts.remove(text)

def check_game_over():
    # Simple check: if no piece fits anywhere
    for piece in current_pieces:
        for y in range(9):
            for x in range(9):
                fits = True
                for dx, dy in piece:
                    nx, ny = x+dx, y+dy
                    if nx>=9 or ny>=9 or board[ny][nx]:
                        fits=False
                        break
                if fits:
                    return False
    return True

def reset_game():
    global board, score, streak, current_pieces, game_over
    board = [[None for _ in range(9)] for _ in range(9)]
    score = 0
    streak = 0
    spawn_pieces()
    game_over=False

# --- Main ---
spawn_pieces()

while True:
    screen.blit(background_img,(0,0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            mx,my = event.pos
            # Select piece
            for i, piece in enumerate(current_pieces):
                px,py = 100 + i*150, SCREEN_HEIGHT-150
                rect = pygame.Rect(px,py, CELL_SIZE*len(piece), CELL_SIZE*len(piece))
                if rect.collidepoint(mx,my):
                    selected_piece = piece
                    drag_offset = (mx-px,my-py)
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and game_over:
            if restart_rect.collidepoint(event.pos):
                reset_game()
        elif event.type == pygame.MOUSEBUTTONUP:
            if selected_piece:
                # Attempt to place piece
                mx,my = event.pos
                bx = (mx - BOARD_OFFSET_X)//CELL_SIZE
                by = (my - BOARD_OFFSET_Y)//CELL_SIZE
                can_place = True
                for dx,dy in selected_piece:
                    nx, ny = bx+dx, by+dy
                    if nx<0 or nx>=9 or ny<0 or ny>=9 or board[ny][nx]:
                        can_place=False
                        break
                if can_place:
                    for dx,dy in selected_piece:
                        nx, ny = bx+dx, by+dy
                        board[ny][nx]=1
                    check_clear()
                    spawn_pieces()  # new 3-piece hand
                    if check_game_over():
                        game_over=True
                selected_piece=None

    # Draw board and effects
    draw_board()
    draw_white_flash()
    update_white_flash()
    update_particles()
    draw_particles()
    draw_score()
    draw_streak_combo()

    # Draw current pieces
    for i,piece in enumerate(current_pieces):
        px,py = 100 + i*150, SCREEN_HEIGHT-150
        scale = CELL_SIZE*1.0
        if selected_piece==piece:
            mx,my = pygame.mouse.get_pos()
            draw_piece(piece,(mx-drag_offset[0], my-drag_offset[1]), scale)
        else:
            draw_piece(piece,(px,py), scale*0.7)

    # Draw highlight for selected piece
    if selected_piece:
        mx,my = pygame.mouse.get_pos()
        bx = (mx - BOARD_OFFSET_X)//CELL_SIZE
        by = (my - BOARD_OFFSET_Y)//CELL_SIZE
        for dx,dy in selected_piece:
            nx, ny = bx+dx, by+dy
            if 0<=nx<9 and 0<=ny<9:
                rect = pygame.Rect(BOARD_OFFSET_X+nx*CELL_SIZE, BOARD_OFFSET_Y+ny*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                screen.blit(highlight_img,rect)

    # Game over
    if game_over:
        font = pygame.font.SysFont(None,72)
        text_surf = font.render("YOU LOSE", True, WHITE)
        screen.blit(text_surf,(SCREEN_WIDTH//2-150, SCREEN_HEIGHT//2-50))
        pygame.draw.rect(screen, WHITE, restart_rect, 2)
        font2 = pygame.font.SysFont(None,36)
        btn_surf = font2.render("RESTART", True, WHITE)
        screen.blit(btn_surf,(restart_rect.x+10,restart_rect.y+5))

    pygame.display.flip()
    clock.tick(FPS)
