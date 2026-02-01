# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.




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

## Architecture: ECS where needed

Use **esper ECS where its natural**. For example in the map, there could be moving NPCs etc. currently theres no need to use ECS everywhere. Game relies mostly to the order
manager, order states, and map ui.



### When NOT to use ECS

- One-off utility functions (file loading, math helpers)
- pygame initialization code
- Build scripts

## Screen Architecture

The game has **three screen types**, each in its own folder:

```
greenwelt/
├── main.py                     # Entry point
├── esper/                      # Bundled ECS library
├── assets/                     # Images, sounds, fonts
├── data/                       # JSON configuration files (roads, locations)
├── requirements.txt            # Dependencies for pygbag
│
├── screens/
│   ├── dialogs/                # Full-screen dialog screens
│   │   ├── start_dialog.py     # Game start / title screen
│   │   ├── start_screen.py     # Game start / title screen
│   │   ├── map_score_dialog.py # Map score display
│   │   ├── score_screen.py     # End game celebration and score display
│   │   ├── abort_screen.py     # Quit confirmation
│   │   ├── conversation.py     # NPC conversation dialogs
│   │   └── phone.py            # Phone UI dialog
│   │
│   ├── map/                    # Top-down world map screen
│   │   ├── map_screen.py           # Main map screen class
│   │   ├── map_ui.py               # Map UI elements (location indicator, phone buttons)
│   │   ├── components.py           # Map-specific ECS components (Camera, RoadLayer, etc.)
│   │   ├── map_render_system.py    # Rendering with camera zoom
│   │   ├── road_collision_system.py # Road collision detection
│   │   └── order_manager.py        # Order management
│   │
│   └── home/                   # Top-down inside-home screen (placeholder)
│       └── home_screen.py
│
├── shared/                     # Shared code across all screens
│   ├── debug_log.py            # Logging utilities
│   ├── debug_overlay.py        # Debug overlay UI
│   ├── fullscreen.py           # Fullscreen toggle (browser/desktop)
│   ├── input_manager.py        # Input handling
│   └── shared_components.py    # Shared ECS components
│
└── tools/                      # Development tools (not bundled in WASM)
    ├── road_painter.py         # Visual road path editor
    ├── map_marker.py           # Location marker tool
    ├── map_order.py            # Order route tool
    └── generate_texts.py       # Text generation helper
```

### Screen Types

1. **Dialog Screens** (`screens/dialogs/`)
   - Full display size, covers entire screen
   - Used for: start, end, abort, scores, conversations, phone UI
   - Text-heavy, button-based interaction

2. **Map Screen** (`screens/map/`)
   - Top-down view of the world
   - Player moves between locations via click-to-move
   - Shows cities, roads, current position
   - Order management for deliveries

3. **Home Screen** (`screens/home/`)
   - Top-down view inside buildings (placeholder)

## Build Commands

```bash
# Build for GitHub Pages (outputs to docs/)
uv run python build.py

# Build and run local test server
uv run python build.py --serve

# Clean build artifacts
uv run python build.py --clean

# Run game locally (native, not WASM)
uv run python main.py

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

If you add some library via `requirements.txt`, it may prevent game loading.
Deploy often and check if after starting you get just black screen,
might be caused by missing library and solution is to bundle it directl into WASM package.

**Pygbag does NOT reliably load packages from PyPI at runtime.** Even if the console shows packages being fetched, they may not be mounted in time for import.

**Solution:** Copy the library source directly into your project folder:

```bash
# Example: bundling esper
cp -r .venv/lib/python3.12/site-packages/esper/ esper/
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

## Screen Resolution

**Fixed resolution: 1920x1080** (Full HD, optimized for tablets)

No scaling system - all sizes are hardcoded for this resolution. This keeps the code simple.

### Standard Sizes

| Element | Size |
|---------|------|
| Screen | 1920x1080 |
| Font small | 36px |
| Font medium | 42px |
| Font large | 52px |
| Button | 200x70 |
| Dialog | ~1400x600 |
| Player dot | radius 24 |
| Map markers | radius 18 |

## Working Configuration

As of January 2026, this configuration works:
- Python 3.12
- uv (package manager)
- pygame-ce >= 2.5.0
- pygbag >= 0.9.2
- esper 3.4 (bundled locally)
- tomli >= 2.0.1 (via requirements.txt)