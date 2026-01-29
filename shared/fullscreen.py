"""
Fullscreen toggle utilities for browser (Pyodide/WASM) and desktop (pygame).
"""
import sys

# Browser fullscreen toggle (Pyodide/pygbag)


def toggle_fullscreen_browser(js=None):
    """
    Toggle fullscreen mode in browser using JS interop (Pyodide/WASM).
    Pass js module if available, otherwise tries to import.
    Returns True if entering fullscreen, False if exiting or failed.
    """
    if js is None:
        try:
            import js as js_mod
            js = js_mod
        except ImportError:
            js = None
    if js is not None:
        try:
            canvas = js.document.getElementById("canvas")
            js.console.log(f"Canvas element: {canvas}")
            js.console.log(
                f"Current fullscreenElement: {js.document.fullscreenElement}")
            if js.document.fullscreenElement:
                js.console.log("Exiting fullscreen...")
                js.document.exitFullscreen()
                return False
            else:
                # Try canvas first
                try:
                    js.console.log("Requesting fullscreen on canvas...")
                    promise = canvas.requestFullscreen()
                    if hasattr(promise, "then"):
                        promise.then(lambda _: js.console.log("Canvas fullscreen success"),
                                     lambda err: js.console.log(f"Canvas fullscreen error: {err}"))
                    return True
                except Exception as e_canvas:
                    js.console.log(f"Canvas fullscreen error: {e_canvas}")
                    # Try document.body
                    try:
                        js.console.log(
                            "Requesting fullscreen on document.body...")
                        promise = js.document.body.requestFullscreen()
                        if hasattr(promise, "then"):
                            promise.then(lambda _: js.console.log("Body fullscreen success"),
                                         lambda err: js.console.log(f"Body fullscreen error: {err}"))
                        return True
                    except Exception as e_body:
                        js.console.log(f"Body fullscreen error: {e_body}")
                        # Try document.documentElement
                        try:
                            js.console.log(
                                "Requesting fullscreen on documentElement...")
                            promise = js.document.documentElement.requestFullscreen()
                            if hasattr(promise, "then"):
                                promise.then(lambda _: js.console.log("DocumentElement fullscreen success"),
                                             lambda err: js.console.log(f"DocumentElement fullscreen error: {err}"))
                            return True
                        except Exception as e_doc:
                            js.console.log(
                                f"DocumentElement fullscreen error: {e_doc}")
                            return False
        except Exception as e:
            js.console.log(f"Fullscreen error: {e}")
            import traceback
            js.console.log(traceback.format_exc())
            return False
    return False

# Desktop fullscreen toggle (pygame)


def toggle_fullscreen_desktop():
    """
    Toggle fullscreen mode in desktop using pygame.
    """
    try:
        import pygame._sdl2.video
        win = pygame._sdl2.video.Window.from_display_module()
        win.fullscreen = not win.fullscreen
    except Exception:
        import pygame
        pygame.display.toggle_fullscreen()
