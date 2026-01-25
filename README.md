# greenwelt

Minimal pygame/esper/pygbag plant courier game.

# Pygbag and pygame-ce

https://github.com/pygame-web
https://pygame-web.github.io/

“pygame running inside a cooperative browser render loop.”

- Engine: a ready-made CPython + pygame-ce compiled to WASM runs in the browser.
- Your code: .py files are shipped as static assets, loaded into a virtual filesystem, then executed.
- Graphics: pygame → SDL2 → browser <canvas> (via Emscripten).
- Rendering: drawing ends up as WebGL or Canvas2D, depending on build.
- FPS: capped by the browser, usually ~60 FPS via requestAnimationFrame (vsync).
- clock.tick(60) is more like a hint; the browser controls timing.
- Performance: fine for 2D games, slower than native, no blocking loops allowed.

- pygbag isn’t “Python compiled to WASM”. Your `.py` stays Python. What’s in WASM is a CPython runtime + C extensions (pygame-ce). ([GitHub][1])
- Build side: the project uses a toolchain (via python-wasm-sdk) to compile CPython (not Pyodide) to WebAssembly with Emscripten, and to compile/link pygame-ce against it. ([GitHub][2])
- Packaging side (what you run locally): `pygbag` takes your project folder (typically `main.py`), bundles your assets, and generates a small HTML/JS loader + manifest so a browser can boot it. ([DeepWiki][3])
- Deployment model: the heavy WASM runtimes are hosted online (CDN/GitHub Pages); the loader downloads the matching runtime/version and caches it (so it’s “download once per version”). ([GitHub][1])
- Runtime in browser: JS bootstraps an Emscripten module, sets up a virtual filesystem (FS), then runs a tiny C “launcher” (often referred to as `pymain`) that embeds CPython and calls into your `main.py`. ([GitHub][2])
- Imports / native deps: pygame is a C extension, so it’s prebuilt as WASM. Since ~0.6, pygbag can load some modules as WASM dynamic libraries (think `.so`-like, but for wasm). ([GitHub][2])
- Rendering/input: pygame-ce ultimately talks to SDL2-in-the-browser (Emscripten’s SDL glue), mapping the pygame “display” to an HTML `<canvas>`, and translating keyboard/mouse/touch events. ([DeepWiki][4])
- Main loop gotcha: browsers need a cooperative event loop (no blocking forever), so many pygbag examples use `asyncio` / yielding so the browser can keep painting frames. ([Jack Whitworth][5])
- TL;DR mental model: “ship a mini CPython+pygame console (WASM) + your game scripts/assets; JS loads it, wires it to canvas/events, then CPython executes your code.” ([DeepWiki][4])

[1]: https://github.com/pygame-web/pygbag?utm_source=chatgpt.com 'GitHub - pygame-web/pygbag: python and pygame wasm for everyone ...'
[2]: https://github.com/pygame-web/pygbag/blob/main/README.md?utm_source=chatgpt.com 'pygbag/README.md at main · pygame-web/pygbag · GitHub'
[3]: https://deepwiki.com/pygame-web/pygbag/3-user-guide?utm_source=chatgpt.com 'User Guide | pygame-web/pygbag | DeepWiki'
[4]: https://deepwiki.com/pygame-web/pygbag/4-architecture?utm_source=chatgpt.com 'Architecture | pygame-web/pygbag | DeepWiki'
[5]: https://jackwhitworth.com/blog/how-to-run-pygame-in-the-browser/?utm_source=chatgpt.com 'How to run Pygame in the browser — Jack Whitworth'
