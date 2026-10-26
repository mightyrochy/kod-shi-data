#!/bin/bash
# opens url in the owner's default Windows browser; URL is not logged
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "Start-Process '$1'" >/dev/null 2>&1
