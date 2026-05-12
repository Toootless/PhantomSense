# GUI Configuration Guide

The PhantomSense GUI can be customized using `gui_config.json`. Edit this file to adjust the layout without modifying the code.

## Configuration Options

### Window Settings (`window`)
- `width`: Window width in pixels (default: 1600)
- `height`: Window height in pixels (default: 900)
- `min_width`: Minimum allowed width (default: 1000)
- `min_height`: Minimum allowed height (default: 700)
- `x`: Window starting X position (default: 50)
- `y`: Window starting Y position (default: 50)

### Layout Settings (`layout`)
- `left_panel_min_width`: Minimum width for left metrics panel (default: 180)
  - **Increase this** if left panel content is too cramped
  - **Decrease this** if you want more space for graphs
- `left_panel_max_width`: Maximum width for left metrics panel (default: 250)
  - Prevents left panel from taking too much space
- `graph_min_height`: Minimum height for graphs (default: 280)
- `unit_min_height`: Minimum height for each unit widget (default: 300)
- `margins`: Outer padding in pixels (default: 12)
- `spacing`: Space between elements in pixels (default: 12)

### Graph Settings (`graph`)
- `width`: Graph label minimum width in pixels (default: 400)
- `height`: Graph label minimum height in pixels (default: 250)
- **To see larger graphs:** Increase both values
- **To fit more on screen:** Decrease both values

### Data Settings (`data`)
- `history_max_samples`: Number of data points to keep in history (default: 50)
- `hub_poll_interval_ms`: How often to fetch data from hub in milliseconds (default: 500)

## Quick Fixes

### "Can't see the left panel metrics"
Increase `left_panel_min_width` from 180 to 220 or 250:
```json
"layout": {
  "left_panel_min_width": 250,
```

### "Graphs are too small"
Increase graph dimensions:
```json
"graph": {
  "width": 600,
  "height": 400,
```

### "Window is too cramped"
Increase window size:
```json
"window": {
  "width": 1920,
  "height": 1080,
```

### "Too much wasted space"
Decrease margins and spacing:
```json
"layout": {
  "margins": 6,
  "spacing": 6,
```

## After Editing

1. Save changes to `gui_config.json`
2. Restart the GUI application
3. Changes take effect immediately

## Default Configuration

See `gui_config.json` for all available options with default values.
