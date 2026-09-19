#!/bin/sh
# Start the Thunder panel (xlp) in background, then run the xlmcp REST/MCP front in foreground.
/xlp &
exec python3 /xlmcp.py serve
