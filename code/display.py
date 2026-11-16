"""Fit the complete game view inside the monitor without stretching it."""

import pico2d.pico2d as sdl

from .settings import SCREEN_HEIGHT, SCREEN_WIDTH


def configure_fullscreen():
    # Desktop fullscreen keeps the monitor's native resolution.
    if sdl.SDL_SetWindowFullscreen(sdl.window, sdl.SDL_WINDOW_FULLSCREEN_DESKTOP) != 0:
        raise RuntimeError(sdl.SDL_GetError().decode("utf-8", errors="replace"))
    if sdl.SDL_RenderSetLogicalSize(sdl.renderer, SCREEN_WIDTH, SCREEN_HEIGHT) != 0:
        raise RuntimeError(sdl.SDL_GetError().decode("utf-8", errors="replace"))


def clear_canvas():
    # Clear the entire output so unused space around the fitted view stays black.
    sdl.SDL_SetRenderDrawColor(sdl.renderer, 0, 0, 0, 255)
    sdl.SDL_RenderClear(sdl.renderer)
