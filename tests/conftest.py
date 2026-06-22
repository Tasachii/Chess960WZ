"""Pytest fixtures and headless setup for the Chess960WZ test suite.

Forces SDL into dummy mode before any pygame import so that incidental
imports never attempt to open a real window or audio device during tests.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
