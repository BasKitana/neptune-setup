local wezterm = require 'wezterm'
local config = wezterm.config_builder()
local act = wezterm.action

-- ==========================================
-- UBUNTU WSL + DEFAULT PROJECTS DIRECTORY
-- ==========================================

config.default_domain = 'local'
config.default_prog = { 'pwsh.exe', '-NoLogo', '-NoExit', '-Command', 'neptune' }

-- ==========================================
-- FROSTED DARK GLASS
-- ==========================================

config.window_background_opacity = 0.30
config.text_background_opacity = 0.45
config.win32_system_backdrop = 'Acrylic'

-- ==========================================
-- COLORS
-- ==========================================

config.colors = {
  foreground = '#F2F5FC',
  background = '#101827',
  cursor_bg = '#8AC7FF',
  cursor_fg = '#101827',
  cursor_border = '#8AC7FF',
  selection_fg = '#FFFFFF',
  selection_bg = '#375B88',
  scrollbar_thumb = '#52627A',
  split = '#6B82A3',

  ansi = {
    '#172234', '#FF7B86', '#81D9AB', '#F4D58A',
    '#83BBFF', '#C5A3FF', '#7ADDE3', '#D8E2F1'
  },

  brights = {
    '#8493AA', '#FFA4AA', '#A5EAC2', '#FFE6AD',
    '#ADD5FF', '#DEC7FF', '#AEF0F2', '#FFFFFF'
  },

  tab_bar = {
    background = '#101827',

    active_tab = {
      bg_color = '#344B69',
      fg_color = '#FFFFFF',
      intensity = 'Bold'
    },

    inactive_tab = {
      bg_color = '#172235',
      fg_color = '#AFBCD0'
    },

    inactive_tab_hover = {
      bg_color = '#293B55',
      fg_color = '#EAF2FF'
    },

    new_tab = {
      bg_color = '#101827',
      fg_color = '#93B9EA'
    },

    new_tab_hover = {
      bg_color = '#293B55',
      fg_color = '#FFFFFF'
    },
  },
}

-- ==========================================
-- FONT
-- ==========================================

config.font = wezterm.font_with_fallback {
  'Cascadia Code',
  'Consolas'
}

config.font_size = 12.0
config.line_height = 1.10

-- ==========================================
-- WINDOW SETTINGS
-- ==========================================

config.initial_cols = 130
config.initial_rows = 36
config.scrollback_lines = 20000
config.enable_scroll_bar = false

config.window_padding = {
  left = 16,
  right = 16,
  top = 12,
  bottom = 12
}

config.window_decorations = 'INTEGRATED_BUTTONS|RESIZE'
config.use_fancy_tab_bar = true
config.hide_tab_bar_if_only_one_tab = false
config.tab_max_width = 28

config.window_frame = {
  font = wezterm.font 'Segoe UI',
  font_size = 11.0,
  active_titlebar_bg = '#101827',
  inactive_titlebar_bg = '#141C2B',
  active_titlebar_fg = '#F2F5FC',
  inactive_titlebar_fg = '#A3B0C5',
  button_fg = '#C4D1E5',
  button_bg = '#101827',
  button_hover_fg = '#FFFFFF',
  button_hover_bg = '#344B69',
}

-- ==========================================
-- CURSOR
-- ==========================================

config.default_cursor_style = 'BlinkingBar'
config.cursor_blink_rate = 650

-- ==========================================
-- COPY / PASTE KEYBOARD SHORTCUTS
-- ==========================================

config.keys = {

  -- Ctrl+C: copy selection or interrupt command
  {
    key = 'c',
    mods = 'CTRL',
    action = wezterm.action_callback(function(window, pane)
      local selection = window:get_selection_text_for_pane(pane)

      if selection ~= '' then
        window:perform_action(act.CopyTo 'Clipboard', pane)
        window:perform_action(act.ClearSelection, pane)
      else
        window:perform_action(
          act.SendKey { key = 'c', mods = 'CTRL' },
          pane
        )
      end
    end),
  },

  -- Ctrl+V: paste
  {
    key = 'v',
    mods = 'CTRL',
    action = act.PasteFrom 'Clipboard',
  },

  -- Ctrl+Shift+C: copy
  {
    key = 'c',
    mods = 'CTRL|SHIFT',
    action = act.CopyTo 'Clipboard',
  },

  -- Ctrl+Shift+V: paste
  {
    key = 'v',
    mods = 'CTRL|SHIFT',
    action = act.PasteFrom 'Clipboard',
  },

  -- Ctrl+Insert: copy
  {
    key = 'Insert',
    mods = 'CTRL',
    action = act.CopyTo 'Clipboard',
  },

  -- Shift+Insert: paste
  {
    key = 'Insert',
    mods = 'SHIFT',
    action = act.PasteFrom 'Clipboard',
  },

  -- Ctrl+Shift+F: search terminal
  {
    key = 'f',
    mods = 'CTRL|SHIFT',
    action = act.Search 'CurrentSelectionOrEmptyString',
  },
}

-- Shift-drag selects in WezTerm even when Herdr captures the mouse.
config.automatically_reload_config = true
config.bypass_mouse_reporting_modifiers = 'SHIFT'
config.mouse_bindings = {
  { event = { Down = { streak = 1, button = 'Left' } }, mods = 'SHIFT',
    action = act.SelectTextAtMouseCursor 'Cell' },
  { event = { Drag = { streak = 1, button = 'Left' } }, mods = 'SHIFT',
    action = act.ExtendSelectionToMouseCursor 'Cell' },
  { event = { Up = { streak = 1, button = 'Left' } }, mods = 'SHIFT',
    action = act.CompleteSelection 'Clipboard' },
}

return config
