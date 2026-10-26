export PATH=/home/rochy/.local/bin:/usr/bin:/bin
cd /mnt/c/tmp/colab-mcp
exec uv run --python 3.13 --with fastmcp==2.14.5 python driver.py >> driver.out 2>&1
