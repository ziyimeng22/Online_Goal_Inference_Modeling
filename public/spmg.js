const { fromEvent } = rxjs;
const { map, filter, pluck, scan, withLatestFrom } = rxjs.operators;

const canvas = document.getElementById('gameCanvas');
const button = document.getElementById('startBtn');
const ctx = canvas.getContext('2d');

const GRID_N = 10;
const CELL = canvas.width / GRID_N; // 50
const playerStart = { x: 0, y: 0 };

const socket = io('http://localhost:3000');

// ── Colors ──────────────────────────────────
const COL = {
    gridBg:    '#151827',
    gridLine:  'rgba(255,255,255,0.04)',
    block:     '#241f3a',
    blockEdge: '#342d52',
    goals:     ['#f59e0b', '#10b981', '#8b5cf6'],
    player:    '#38bdf8',
    trail:     'rgba(56,189,248,',
    text:      '#ffffff',
};
const GLABELS = ['G\u2081','G\u2082','G\u2083'];

let goals = [];
let blocks = [];
let currentPos = { ...playerStart };
let visitedCells = [];

// ── Connection status ───────────────────────
const statusEl = document.getElementById('status');
socket.on('connect', () => {
    statusEl.textContent = 'Connected';
    statusEl.classList.add('connected');
});
socket.on('disconnect', () => {
    statusEl.textContent = 'Disconnected';
    statusEl.classList.remove('connected');
});

// ── Drawing helpers ─────────────────────────
function rr(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x+r, y);
    ctx.arcTo(x+w, y, x+w, y+h, r);
    ctx.arcTo(x+w, y+h, x, y+h, r);
    ctx.arcTo(x, y+h, x, y, r);
    ctx.arcTo(x, y, x+w, y, r);
    ctx.closePath();
}

function drawGrid() {
    ctx.fillStyle = COL.gridBg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = COL.gridLine;
    ctx.lineWidth = 1;
    for (let i = 0; i <= GRID_N; i++) {
        ctx.beginPath();
        ctx.moveTo(i * CELL, 0);
        ctx.lineTo(i * CELL, canvas.height);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(0, i * CELL);
        ctx.lineTo(canvas.width, i * CELL);
        ctx.stroke();
    }
}

function drawBlocks() {
    blocks.forEach(b => {
        const px = b.x * CELL + 1.5, py = b.y * CELL + 1.5, sz = CELL - 3;
        rr(px, py, sz, sz, 4);
        ctx.fillStyle = COL.block;
        ctx.fill();
        ctx.strokeStyle = COL.blockEdge;
        ctx.lineWidth = 0.5;
        ctx.stroke();
    });
}

function drawGoals() {
    goals.forEach((g, i) => {
        const px = g.x * CELL, py = g.y * CELL;
        const pv = g.posterior || (1 / 3);

        // Glow
        ctx.save();
        ctx.shadowColor = COL.goals[i];
        ctx.shadowBlur = 6 + pv * 16;
        rr(px + 3, py + 3, CELL - 6, CELL - 6, 6);
        ctx.fillStyle = COL.goals[i];
        ctx.globalAlpha = 0.15 + pv * 0.6;
        ctx.fill();
        ctx.restore();

        // Solid
        rr(px + 2, py + 2, CELL - 4, CELL - 4, 5);
        ctx.fillStyle = COL.goals[i];
        ctx.globalAlpha = 0.2 + pv * 0.55;
        ctx.fill();
        ctx.globalAlpha = 1;

        // Label
        ctx.fillStyle = COL.text;
        ctx.globalAlpha = 0.6 + pv * 0.4;
        ctx.font = 'bold 16px -apple-system, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(GLABELS[i], px + CELL / 2, py + CELL / 2);
        ctx.globalAlpha = 1;
    });
}

function drawTrail() {
    for (let i = 0; i < visitedCells.length; i++) {
        const age = visitedCells.length - 1 - i;
        const alpha = Math.max(0.02, 0.2 - age * 0.01);
        const c = visitedCells[i];
        rr(c.x * CELL + 2, c.y * CELL + 2, CELL - 4, CELL - 4, 4);
        ctx.fillStyle = COL.trail + alpha + ')';
        ctx.fill();
    }
}

function drawPlayer(pos) {
    const px = pos.x * CELL + CELL / 2;
    const py = pos.y * CELL + CELL / 2;

    // Glow
    ctx.save();
    ctx.shadowColor = COL.player;
    ctx.shadowBlur = 18;
    ctx.beginPath();
    ctx.arc(px, py, CELL * 0.35, 0, Math.PI * 2);
    ctx.fillStyle = COL.player;
    ctx.fill();
    ctx.restore();

    // Inner highlight
    ctx.beginPath();
    ctx.arc(px, py, CELL * 0.15, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    ctx.fill();
}

function render(pos) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawGrid();
    drawTrail();
    drawBlocks();
    drawGoals();
    drawPlayer(pos);
}

// ── Update posterior bars in DOM ─────────────
function updatePosteriorUI(posterior) {
    const vals = [posterior.G1, posterior.G2, posterior.G3];
    for (let i = 0; i < 3; i++) {
        const pct = (vals[i] * 100).toFixed(1);
        document.getElementById('bar' + (i + 1)).style.width = pct + '%';
        document.getElementById('val' + (i + 1)).textContent = pct + '%';
        if (goals[i]) goals[i].posterior = vals[i];
    }
}

// ── Game logic ──────────────────────────────
function isReached(pos) {
    return goals.some(g => g.x === pos.x && g.y === pos.y);
}

const playerReady$ = fromEvent(button, 'click');
playerReady$.subscribe(() => {
    socket.emit('playerReady', 'Player is ready!');
});

socket.on('initializeGame', function (game_map) {
    goals = game_map.goals.map((g, i) => ({
        x: g[0], y: g[1], posterior: 1 / 3
    }));
    blocks = game_map.blocks.map(b => ({ x: b[0], y: b[1] }));

    currentPos = { ...playerStart };
    visitedCells = [];
    updatePosteriorUI({ G1: 1/3, G2: 1/3, G3: 1/3 });
    render(currentPos);

    const subscription = action_position$.subscribe(({ action, position }) => {
        visitedCells.push({ ...currentPos });
        currentPos = position;
        render(position);

        if (isReached(position)) {
            alert('Goal reached! Click Start Game for the next trial.');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            drawGrid();
            subscription.unsubscribe();
            goals.length = 0;
            blocks.length = 0;
            visitedCells = [];
            updatePosteriorUI({ G1: 1/3, G2: 1/3, G3: 1/3 });
        }
        socket.emit('updatePrior', { action, position });
    });
});

// ── Movement ────────────────────────────────
const movement$ = fromEvent(document, 'keydown').pipe(
    pluck('code'),
    filter(code => ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(code)),
    map(code => {
        switch (code) {
            case 'ArrowLeft':  return { x: -1, y: 0 };
            case 'ArrowRight': return { x: 1, y: 0 };
            case 'ArrowUp':    return { x: 0, y: -1 };
            case 'ArrowDown':  return { x: 0, y: 1 };
            default:           return { x: 0, y: 0 };
        }
    })
);

const updatePlayerPos$ = movement$.pipe(
    scan((pos, mv) => {
        let np = {
            x: Math.max(0, Math.min(GRID_N - 1, pos.x + mv.x)),
            y: Math.max(0, Math.min(GRID_N - 1, pos.y + mv.y))
        };
        if (blocks.some(b => b.x === np.x && b.y === np.y)) np = pos;
        return np;
    }, playerStart)
);

const action_position$ = movement$.pipe(
    withLatestFrom(updatePlayerPos$),
    map(([action, pos]) => ({
        action: [action.x, action.y],
        position: pos
    }))
);

// ── Posterior from server ───────────────────
socket.on('updatePosterior', function (posterior) {
    updatePosteriorUI(posterior);
    render(currentPos);
});
