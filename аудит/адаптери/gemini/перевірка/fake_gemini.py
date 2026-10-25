#!/usr/bin/env python3
import os, runpy
os.environ['FAKE_KIND'] = 'gemini'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fake_cli.py'), run_name='__main__')
