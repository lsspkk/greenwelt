# Plant Courier - WASM/Pygbag Project

## Code Style Guidelines

**Write code for Python novices.** Prioritize readability over cleverness.

### Principles

1. **Simple classes over complex methods** - Break code into many small, focused classes
2. **Long methods are OK** - A 50-line straightforward method is better than 5 clever 10-line methods
3. **Avoid Python magic** - No metaclasses, decorators with arguments, or complex comprehensions
4. **Explicit over implicit** - Name things clearly, avoid abbreviations
5. **One class per file when possible** - Easy to find, easy to understand

### What to avoid

```python
# BAD: Too clever
entities = [e for e in world.get_entities() if hasattr(e, 'pos') and e.pos.x > 0]

# GOOD: Clear and simple
entities = []
for entity in world.get_entities():
    if hasattr(entity, 'pos'):
        if entity.pos.x > 0:
            entities.append(entity)
```

```python
# BAD: Dense one-liner
def get_closest(self, pos): return min(self.targets, key=lambda t: (t.x-pos.x)**2+(t.y-pos.y)**2)

# GOOD: Step by step
def get_closest(self, pos):
    closest_target = None
    closest_distance = float('inf')

    for target in self.targets:
        dx = target.x - pos.x
        dy = target.y - pos.y
        distance = dx * dx + dy * dy

        if distance < closest_distance:
            closest_distance = distance
            closest_target = target

    return closest_target
```

## Architecture: ECS-First Design

Use **esper ECS for almost everything**. Game state lives in components, logic lives in systems.

### Components (data only)

```python
class Position:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

class Health:
    def __init__(self, current: int, maximum: int):
        self.current = current
        self.maximum = maximum
```

### Systems (logic only)

```python
class MovementSystem(esper.Processor):
    def process(self, dt: float):
        for ent, (pos, vel) in self.world.get_components(Position, Velocity):
            pos.x = pos.x + vel.vx * dt
            pos.y = pos.y + vel.vy * dt
```

### When NOT to use ECS

- One-off utility functions (file loading, math helpers)
- pygame initialization code
- Build scripts

## Screen Architecture

The game has **three screen types**, each in its own folder:

```
src/
├── main.py                     # Entry point
├── esper/                      # Bundled ECS library
├── assets/                     # Images, sounds, fonts
├── data/                       # TOML configuration files
├── requirements.txt            # Dependencies for pygbag
│
├── screens/
│   ├── __init__.py
│   │
│   ├── dialog/                 # Full-screen dialog screens
│   │   ├── __init__.py
│   │   ├── base_dialog.py      # Base class for all dialogs
│   │   ├── start_screen.py     # Game start / title screen
│   │   ├── score_screen.py     # End game score display
│   │   ├── abort_screen.py     # Quit confirmation
│   │   ├── conversation.py     # NPC conversation dialogs
│   │   └── components/         # Dialog-specific ECS components
│   │       └── __init__.py
│   │
│   ├── map/                    # Top-down world map screen
│   │   ├── __init__.py
│   │   ├── map_screen.py       # Main map screen class
│   │   ├── systems/            # Map-specific ECS systems
│   │   │   └── __init__.py
│   │   └── components/         # Map-specific ECS components
│   │       └── __init__.py
│   │
│   └── home/                   # Top-down inside-home screen
│       ├── __init__.py
│       ├── home_screen.py      # Main home screen class
│       ├── systems/            # Home-specific ECS systems
│       │   └── __init__.py
│       └── components/         # Home-specific ECS components
│           └── __init__.py
│
└── shared/                     # Shared code across all screens
    ├── __init__.py
    ├── components/             # Shared ECS components
    │   └── __init__.py
    └── systems/                # Shared ECS systems
        └── __init__.py
```

### Screen Types

1. **Dialog Screens** (`screens/dialog/`)
   - Full display size, covers entire screen
   - Used for: start screen, score screen, abort confirmation, NPC conversations
   - Text-heavy, button-based interaction
   - Reusable dialog components

2. **Map Screen** (`screens/map/`)
   - Top-down view of the world
   - Player moves between locations
   - Shows cities, roads, current position

3. **Home Screen** (`screens/home/`)
   - Top-down view inside buildings
   - Player interacts with objects and NPCs
   - Interior navigation

## Build Commands

```bash
# Build for GitHub Pages (outputs to docs/)
uv run python build.py

# Build and run local test server
uv run python build.py --serve

# Clean build artifacts
uv run python build.py --clean

# Run game locally (native, not WASM)
uv run python src/main.py

# Add a dependency
uv add package-name

# Sync dependencies
uv sync
```

## GitHub Pages Deployment

1. Run `uv run python build.py` to generate the `docs/` folder
2. Commit and push the `docs/` folder to your repository
3. Go to repository Settings > Pages
4. Set Source to "Deploy from a branch"
5. Select branch `main` and folder `/docs`
6. Save and wait for deployment

## WASM/Pygbag Critical Requirements

### 1. Bundle Third-Party Libraries Directly

**Pygbag does NOT reliably load packages from PyPI at runtime.** Even if the console shows packages being fetched, they may not be mounted in time for import.

**Solution:** Copy the library source directly into your project folder:

```bash
# Example: bundling esper
cp -r .venv/lib/python3.12/site-packages/esper/ src/esper/
```

Then remove from `requirements.txt` since it's now bundled.

**Libraries confirmed to need bundling:**
- `esper` - ECS library (pure Python, works when bundled)

**Libraries that work via requirements.txt:**
- `pygame-ce` - handled specially by pygbag
- `tomli` - TOML parser (fetched from pygbag repo)

### 2. Async Main Loop Pattern

The main game loop MUST be async and yield control:

```python
import asyncio
import pygame

async def main():
    pygame.init()
    screen = pygame.display.set_mode((480, 320))
    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Game logic here

        pygame.display.flip()
        await asyncio.sleep(0)  # CRITICAL: yield to browser

if __name__ == '__main__':
    asyncio.run(main())
```

### 3. Entry Point Must Be `main.py`

Pygbag looks for `main.py` in the root of the packaged folder.

### 4. Avoid Print Statements in Production

Print statements severely degrade WASM performance. Remove all debug `print()` calls before deployment.

### 5. File Path Handling

`Path(__file__)` works but paths resolve differently in WASM. Test file loading in browser.

## Debugging WASM Issues

When something doesn't work in browser but works locally:

1. **Check browser console (F12)** for JavaScript errors
2. **Render debug info on screen** - Python print() may not appear in browser console
3. **Test imports individually** with try/except and display results on pygame surface
4. **Bundle the library locally** if import fails with "ModuleNotFoundError"

## Working Configuration

As of January 2026, this configuration works:
- Python 3.12
- uv (package manager)
- pygame-ce >= 2.5.0
- pygbag >= 0.9.2
- esper 3.4 (bundled locally)
- tomli >= 2.0.1 (via requirements.txt)