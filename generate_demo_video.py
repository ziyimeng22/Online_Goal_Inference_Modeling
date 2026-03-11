"""
Generate a 280x180 demo video of Bayesian Goal Inference.
Renders at 3x (840x540) then downscales for quality.
Output: public/demo_280x180.mp4
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio
import math
import os

# ════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════
SCALE = 2                       # internal supersample factor
W, H = 840 * SCALE, 540 * SCALE  # 1680 x 1080
OUT_W, OUT_H = 280, 180
HI_W, HI_H = 840, 540           # high-res output
FPS = 30

# Colors (RGB)
BG         = (15, 17, 23)
PANEL_BG   = (18, 20, 30)
GRID_BG    = (21, 24, 39)
GRID_LINE  = (30, 33, 48)
BLOCK      = (36, 31, 58)
BLOCK_EDGE = (52, 45, 82)
PLAYER     = (56, 189, 248)
PLAYER_IN  = (200, 230, 255)
TRAIL      = (56, 189, 248)
TEXT       = (226, 232, 240)
TEXT_SEC   = (148, 163, 184)
TEXT_MUTED = (87, 94, 112)
DIVIDER    = (35, 38, 52)
BAR_TRACK  = (25, 28, 42)
GOALS_C    = [(245, 158, 11), (16, 185, 129), (139, 92, 246)]
GLABELS    = ['G₁', 'G₂', 'G₃']

# Layout (all scaled)
GX, GY = 28 * SCALE, 52 * SCALE
GS = 420 * SCALE
CELL = GS // 10
GRID_N = 10
PX = 478 * SCALE
PW = 335 * SCALE

# ════════════════════════════════════════════
# DEMO DATA
# ════════════════════════════════════════════
BLOCKS = [(4,1),(4,2),(4,3),(4,5),(4,6),(4,7),(4,8),(4,9)]
GOALS  = [(0,9),(9,0),(9,9)]

PATH = [
    (0,0),(1,0),(2,0),(3,0),(4,0),(5,0),
    (5,1),(5,2),(5,3),(6,3),(6,4),(7,4),
    (7,5),(8,5),(8,6),(9,6),(9,7),(9,8),(9,9)
]

POST = [
    (.333,.333,.333),(.18,.41,.41),(.08,.46,.46),(.04,.48,.48),
    (.02,.49,.49),(.01,.49,.50),(.01,.40,.59),(.01,.32,.67),
    (.01,.25,.74),(.01,.20,.79),(.01,.15,.84),(.01,.12,.87),
    (.01,.09,.90),(.01,.07,.92),(.01,.05,.94),(.01,.04,.95),
    (.01,.03,.96),(.01,.02,.97),(.01,.01,.98)
]

# Timing (in seconds)
MOVE_DUR  = 0.48
WAIT_DUR  = 0.38
INIT_WAIT = 1.2
DONE_WAIT = 2.6
RESET_WAIT = 1.0

# ════════════════════════════════════════════
# FONT SETUP
# ════════════════════════════════════════════
def load_font(size, bold=False):
    """Try to load a nice system font, fall back to default."""
    candidates = [
        '/System/Library/Fonts/SFNSText.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/SFNSDisplay.ttf',
        '/Library/Fonts/Arial.ttf',
        '/System/Library/Fonts/Supplemental/Arial.ttf',
    ]
    bold_candidates = [
        '/System/Library/Fonts/SFNSText-Bold.ttf',
        '/Library/Fonts/Arial Bold.ttf',
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    ]
    serif_candidates = [
        '/Library/Fonts/Georgia.ttf',
        '/System/Library/Fonts/Supplemental/Georgia.ttf',
        '/Library/Fonts/Times New Roman.ttf',
        '/System/Library/Fonts/Supplemental/Times New Roman.ttf',
    ]

    search = bold_candidates + candidates if bold else candidates
    for path in search:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

def load_unicode(size):
    """Load a font with good Unicode coverage (subscripts, math symbols)."""
    candidates = [
        '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
        '/Library/Fonts/Arial Unicode.ttf',
        '/System/Library/Fonts/SFNS.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return load_font(size)

def load_serif(size):
    candidates = [
        '/Library/Fonts/Georgia Italic.ttf',
        '/System/Library/Fonts/Supplemental/Georgia Italic.ttf',
        '/Library/Fonts/Georgia.ttf',
        '/System/Library/Fonts/Supplemental/Georgia.ttf',
        '/Library/Fonts/Times New Roman Italic.ttf',
        '/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf',
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return load_font(size)

# Pre-load fonts (all sizes scaled)
S = SCALE
FONT_TITLE = load_font(11*S, bold=True)
FONT_LABEL = load_unicode(14*S)       # needs subscript digits
FONT_LABEL_BOLD = load_font(14*S, bold=True)
FONT_LABEL_SM = load_font(13*S, bold=True)
FONT_TEXT = load_font(12*S)
FONT_TEXT_SM = load_font(11*S)
FONT_TEXT_XS = load_font(10*S)
FONT_VAL = load_font(12*S)
FONT_MATH = load_unicode(16*S)        # needs ∝, subscripts
FONT_MATH_SM = load_unicode(14*S)
FONT_MATH_XS = load_unicode(10*S)
FONT_NOTE = load_font(11*S)
FONT_PLAYER_LABEL = load_unicode(13*S) # needs subscript digits

# ════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════
def ease(t):
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2*t + 2)**3 / 2

def lerp(a, b, t):
    return a + (b - a) * t

def alpha_blend(bg, fg, alpha):
    """Blend fg color over bg with alpha (0-1)."""
    return tuple(int(b + (f - b) * alpha) for b, f in zip(bg, fg))

def draw_rounded_rect(draw, xy, fill, radius=4, outline=None, width=0):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = xy
    # Ensure valid dimensions
    if x2 <= x1 or y2 <= y1:
        return
    rw = (x2 - x1) / 2
    rh = (y2 - y1) / 2
    r = min(radius, int(rw), int(rh))
    if r < 1:
        draw.rectangle([x1, y1, x2, y2], fill=fill, outline=outline, width=width)
        return
    # Use pieslice for corners + rectangles for body
    if fill:
        draw.pieslice([x1, y1, x1+2*r, y1+2*r], 180, 270, fill=fill)
        draw.pieslice([x2-2*r, y1, x2, y1+2*r], 270, 360, fill=fill)
        draw.pieslice([x1, y2-2*r, x1+2*r, y2], 90, 180, fill=fill)
        draw.pieslice([x2-2*r, y2-2*r, x2, y2], 0, 90, fill=fill)
        if x1+r < x2-r:
            draw.rectangle([x1+r, y1, x2-r, y2], fill=fill)
        if y1+r < y2-r:
            draw.rectangle([x1, y1+r, x1+r, y2-r], fill=fill)
            draw.rectangle([x2-r, y1+r, x2, y2-r], fill=fill)
    if outline and width:
        draw.line([(x1+r, y1), (x2-r, y1)], fill=outline, width=width)
        draw.line([(x1+r, y2), (x2-r, y2)], fill=outline, width=width)
        draw.line([(x1, y1+r), (x1, y2-r)], fill=outline, width=width)
        draw.line([(x2, y1+r), (x2, y2-r)], fill=outline, width=width)


# ════════════════════════════════════════════
# FRAME RENDERER
# ════════════════════════════════════════════
def render_frame(step, move_progress, disp_post, trail_indices, time_s):
    """Render one frame, return PIL Image at WxH (supersampled)."""
    s = SCALE  # shorthand
    img = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(img)

    # ── Title & rules ──
    draw.text((W//2, 20*s), 'ONLINE  BAYESIAN  GOAL  INFERENCE', fill=TEXT_MUTED,
              font=FONT_TITLE, anchor='mt')
    draw.line([(28*s, 40*s), (W-28*s, 40*s)], fill=DIVIDER, width=s)
    draw.line([(28*s, H-18*s), (W-28*s, H-18*s)], fill=DIVIDER, width=s)
    draw.text((W-30*s, H-8*s), 'Baker et al. 2009 · Zhi-Xuan et al. 2020', fill=TEXT_MUTED,
              font=FONT_TEXT_XS, anchor='rb')

    # ── Grid background ──
    draw_rounded_rect(draw, (GX-s, GY-s, GX+GS+s, GY+GS+s), fill=GRID_BG, radius=5*s)

    # ── Grid lines ──
    for i in range(GRID_N + 1):
        draw.line([(GX + i*CELL, GY), (GX + i*CELL, GY+GS)], fill=GRID_LINE, width=s)
        draw.line([(GX, GY + i*CELL), (GX+GS, GY + i*CELL)], fill=GRID_LINE, width=s)

    # ── Trail ──
    for idx, ti in enumerate(trail_indices):
        age = len(trail_indices) - 1 - idx
        alpha = max(0.03, 0.25 - age * 0.013)
        cx, cy = PATH[ti]
        col = alpha_blend(GRID_BG, TRAIL, alpha)
        px, py = GX + cx*CELL + 2*s, GY + cy*CELL + 2*s
        draw_rounded_rect(draw, (px, py, px+CELL-4*s, py+CELL-4*s), fill=col, radius=3*s)

    # ── Blocks ──
    for bx, by in BLOCKS:
        px, py = GX + bx*CELL + 2*s, GY + by*CELL + 2*s
        draw_rounded_rect(draw, (px, py, px+CELL-4*s, py+CELL-4*s), fill=BLOCK, radius=3*s,
                          outline=BLOCK_EDGE, width=s)

    # ── Goals ──
    pulse = 0.5 + 0.5 * math.sin(time_s * 3.5)
    for i, (gx, gy) in enumerate(GOALS):
        pv = disp_post[i]
        px, py = GX + gx*CELL, GY + gy*CELL

        glow_alpha = 0.12 + pv * 0.55 + pulse * 0.06
        goal_fill = alpha_blend(GRID_BG, GOALS_C[i], min(1.0, glow_alpha))
        draw_rounded_rect(draw, (px+2*s, py+2*s, px+CELL-2*s, py+CELL-2*s),
                          fill=goal_fill, radius=5*s)

        if pv > 0.4:
            border_col = alpha_blend(goal_fill, GOALS_C[i], 0.5)
            draw_rounded_rect(draw, (px+2*s, py+2*s, px+CELL-2*s, py+CELL-2*s),
                              fill=None, radius=5*s, outline=border_col, width=s)

        label_alpha = 0.55 + pv * 0.45
        label_col = alpha_blend(goal_fill, (255, 255, 255), label_alpha)
        draw.text((px + CELL//2, py + CELL//2), GLABELS[i], fill=label_col,
                  font=FONT_PLAYER_LABEL, anchor='mm')

    # ── Player ──
    if move_progress < 1.0 and step > 0:
        fx, fy = PATH[step - 1]
        tx, ty = PATH[step]
        e = ease(move_progress)
        player_px = GX + lerp(fx, tx, e) * CELL + CELL // 2
        player_py = GY + lerp(fy, ty, e) * CELL + CELL // 2
    else:
        cx, cy = PATH[min(step, len(PATH) - 1)]
        player_px = GX + cx * CELL + CELL // 2
        player_py = GY + cy * CELL + CELL // 2

    # Player glow layers (more layers at higher scale = smoother glow)
    for r_off, a in [(22*s, 0.05), (18*s, 0.08), (14*s, 0.12), (10*s, 0.17), (7*s, 0.24)]:
        glow_col = alpha_blend(GRID_BG, PLAYER, a)
        draw.ellipse([player_px - r_off, player_py - r_off,
                      player_px + r_off, player_py + r_off], fill=glow_col)

    pr = int(CELL * 0.33)
    draw.ellipse([player_px - pr, player_py - pr,
                  player_px + pr, player_py + pr], fill=PLAYER)

    pir = int(CELL * 0.14)
    draw.ellipse([player_px - pir, player_py - pir,
                  player_px + pir, player_py + pir], fill=PLAYER_IN)

    # ── Right Panel ──
    draw_rounded_rect(draw, (PX-8*s, GY-s, PX+PW+8*s, GY+GS+s), fill=PANEL_BG, radius=5*s)

    lx = PX + 12*s
    rx = PX + PW + 2*s
    y = GY + 16*s

    # Section: Math
    draw.text((lx, y), 'BAYESIAN  INFERENCE', fill=TEXT_MUTED, font=FONT_TITLE)
    y += 28*s

    draw.text((lx, y), 'P(G | a₁:t) ∝ P(a₁:t | G) · P(G)', fill=TEXT, font=FONT_MATH)
    y += 30*s

    draw.text((lx, y), 'P(a | s, G) ∝ exp( Q(s,a,G) / τ )', fill=TEXT_SEC, font=FONT_MATH_SM)
    y += 24*s

    draw.text((lx, y), 'τ = 5   (bounded rationality)', fill=TEXT_MUTED, font=FONT_NOTE)
    y += 16*s
    draw.text((lx, y), 'λ = 0.9  (prior temporal decay)', fill=TEXT_MUTED, font=FONT_NOTE)
    y += 20*s

    draw.line([(PX, y), (PX + PW, y)], fill=DIVIDER, width=s)
    y += 20*s

    draw.text((lx, y), 'POSTERIOR   P(G | actions)', fill=TEXT_MUTED, font=FONT_TITLE)
    y += 26*s

    bar_w = PW - 80*s
    bar_h = 26*s
    gap = 18*s

    for i in range(3):
        by = y + i * (bar_h + gap)
        bx = lx + 35*s

        draw.text((lx, by + bar_h // 2), GLABELS[i], fill=GOALS_C[i],
                  font=FONT_LABEL, anchor='lm')

        draw_rounded_rect(draw, (bx, by, bx + bar_w, by + bar_h),
                          fill=BAR_TRACK, radius=5*s)

        fw = max(3*s, int(bar_w * disp_post[i]))
        draw_rounded_rect(draw, (bx, by, bx + fw, by + bar_h),
                          fill=GOALS_C[i], radius=5*s)

        pct = f'{disp_post[i]*100:.1f}%'
        draw.text((rx, by + bar_h // 2), pct, fill=TEXT, font=FONT_VAL, anchor='rm')

    # Step progress bar
    y += 3 * (bar_h + gap) + 18*s
    sb_w = PW - 10*s
    sb_h = 4*s
    draw_rounded_rect(draw, (lx, y, lx + sb_w, y + sb_h), fill=BAR_TRACK, radius=2*s)
    prog = step / (len(PATH) - 1)
    prog_w = max(8*s, int(sb_w * prog))
    prog_col = alpha_blend(PANEL_BG, PLAYER, 0.5)
    if prog_w > 8*s:
        draw_rounded_rect(draw, (lx, y, lx + prog_w, y + sb_h), fill=prog_col, radius=2*s)
    else:
        draw.rectangle([lx, y, lx + prog_w, y + sb_h], fill=prog_col)

    y += 16*s
    draw.text((lx, y), f'Step {step} / {len(PATH)-1}', fill=TEXT_MUTED, font=FONT_TEXT)

    # Legend
    y += 28*s
    draw.text((lx, y), '●', fill=PLAYER, font=FONT_TEXT_XS)
    draw.text((lx + 10*s, y), 'Agent', fill=TEXT_MUTED, font=FONT_TEXT_XS)
    draw.text((lx + 68*s, y), '■', fill=GOALS_C[0], font=FONT_TEXT_XS)
    draw.text((lx + 78*s, y), 'Goal', fill=TEXT_MUTED, font=FONT_TEXT_XS)
    draw.text((lx + 130*s, y), '■', fill=BLOCK_EDGE, font=FONT_TEXT_XS)
    draw.text((lx + 140*s, y), 'Obstacle', fill=TEXT_MUTED, font=FONT_TEXT_XS)

    return img


# ════════════════════════════════════════════
# ANIMATION TIMELINE
# ════════════════════════════════════════════
def generate_frames():
    """Generate all frames for one full loop."""
    frames = []
    disp_post = list(POST[0])
    trail = []

    total_steps = len(PATH) - 1  # 18 moves

    # Phase 1: Initial wait
    n_init = int(INIT_WAIT * FPS)
    for f in range(n_init):
        t = f / FPS
        img = render_frame(0, 1.0, disp_post, trail, t)
        frames.append(img)

    time_offset = INIT_WAIT

    # Phase 2: Steps
    for s in range(1, len(PATH)):
        targ = list(POST[s])
        trail.append(s - 1)

        # Moving phase
        n_move = int(MOVE_DUR * FPS)
        for f in range(n_move):
            prog = f / n_move
            # Smooth posterior interpolation
            for i in range(3):
                disp_post[i] += (targ[i] - disp_post[i]) * 0.12
            t = time_offset + f / FPS
            img = render_frame(s, prog, disp_post, trail, t)
            frames.append(img)

        # Waiting phase
        n_wait = int(WAIT_DUR * FPS)
        for f in range(n_wait):
            for i in range(3):
                disp_post[i] += (targ[i] - disp_post[i]) * 0.12
            t = time_offset + MOVE_DUR + f / FPS
            img = render_frame(s, 1.0, disp_post, trail, t)
            frames.append(img)

        time_offset += MOVE_DUR + WAIT_DUR

    # Phase 3: Goal reached pause
    trail.append(len(PATH) - 1)
    # Let posterior fully converge
    targ = list(POST[-1])
    n_done = int(DONE_WAIT * FPS)
    for f in range(n_done):
        for i in range(3):
            disp_post[i] += (targ[i] - disp_post[i]) * 0.15
        t = time_offset + f / FPS
        img = render_frame(len(PATH) - 1, 1.0, disp_post, trail, t)
        frames.append(img)

    return frames


# ════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════
if __name__ == '__main__':
    print('Generating frames...')
    frames = generate_frames()
    print(f'  {len(frames)} frames generated ({len(frames)/FPS:.1f}s at {FPS}fps)')

    base = os.path.join(os.path.dirname(__file__), 'public')

    # ── High-res output (840x540) ──
    print('Downscaling to 840x540 (high-res)...')
    hi_frames = []
    for i, f in enumerate(frames):
        hi = f.resize((HI_W, HI_H), Image.LANCZOS)
        hi_frames.append(np.array(hi))

    hi_path = os.path.join(base, 'demo_840x540.mp4')
    print(f'Writing {hi_path}...')
    writer = imageio.get_writer(hi_path, fps=FPS, quality=10, format='FFMPEG', codec='libx264',
                                pixelformat='yuv420p', macro_block_size=1)
    for frame in hi_frames:
        writer.append_data(frame)
    writer.close()

    # ── Standard output (280x180) ──
    print('Downscaling to 280x180...')
    small_frames = []
    for i, f in enumerate(frames):
        small = f.resize((OUT_W, OUT_H), Image.LANCZOS)
        small_frames.append(np.array(small))

    out_path = os.path.join(base, 'demo_280x180.mp4')
    print(f'Writing {out_path}...')
    writer = imageio.get_writer(out_path, fps=FPS, quality=10, format='FFMPEG', codec='libx264',
                                pixelformat='yuv420p', macro_block_size=1)
    for frame in small_frames:
        writer.append_data(frame)
    writer.close()

    # ── GIF (280x180, every 2nd frame) ──
    gif_path = os.path.join(base, 'demo_280x180.gif')
    print(f'Writing {gif_path}...')
    gif_frames = small_frames[::2]
    imageio.mimsave(gif_path, gif_frames, fps=FPS//2, loop=0)

    # ── Preview PNG at 840x540 ──
    preview_path = os.path.join(base, 'demo_preview.png')
    mid = len(frames) // 2
    frames[mid].resize((HI_W, HI_H), Image.LANCZOS).save(preview_path)

    print(f'Done!')
    print(f'  Hi-res MP4 : {hi_path} ({os.path.getsize(hi_path)/1024:.0f} KB)')
    print(f'  280x180 MP4: {out_path} ({os.path.getsize(out_path)/1024:.0f} KB)')
    print(f'  280x180 GIF: {gif_path} ({os.path.getsize(gif_path)/1024:.0f} KB)')
    print(f'  Preview    : {preview_path}')
