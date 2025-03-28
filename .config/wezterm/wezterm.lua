local wezterm = require("wezterm")
local config = {}
local home = os.getenv("HOME") or os.getenv("USERPROFILE")

if wezterm.config_builder then
  config = wezterm.config_builder()
end

config = {
  default_cursor_style = "SteadyBlock",
  automatically_reload_config = true,
  window_close_confirmation = "NeverPrompt",
  adjust_window_size_when_changing_font_size = false,
  window_decorations = "RESIZE",
  check_for_updates = false,
  use_fancy_tab_bar = false,
  tab_bar_at_bottom = false,
  font_size = 22,
  font = wezterm.font("JetBrains Mono", { weight = "Bold" }),
  enable_tab_bar = true,
  window_padding = {
    left = 3,
    right = 3,
    top = 0,
    bottom = 0,
  },
  -- Make pane splits more apparent by dimming inactive panes
  inactive_pane_hsb = {
    saturation = 0.8,
    brightness = 0.3,
  },
  -- Add colors configuration to make pane borders more visible
  colors = {
    tab_bar = {
      background = '#1f2730',
      active_tab = {
        bg_color = "#993333",
        fg_color = "#cccccc",
      },
      inactive_tab = {
        bg_color = "#1f2730",
        fg_color = "#707070",
      },
    },
  },
  window_frame = {
    -- Background color when the window is active/focused
    active_titlebar_bg = '#333333',
    
    -- Background color when the window is inactive
    inactive_titlebar_bg = '#2b2042',
    
    -- Optional: customize the font used in the title bar
    font = wezterm.font { family = 'Roboto', weight = 'Bold' },
    font_size = 22.0,
  },
  background = {
    {
      source = {
        File = home .. "/dev/dotfiles/img/Dome.png",
      },
      hsb = {
        hue = 1.0,
        saturation = 1.02,
        brightness = 0.15,
      },
      width = "100%",
      height = "100%",
    },
    {
      source = {
        Color = "#282c35",
      },
      width = "100%",
      height = "100%",
      opacity = 0.55,
    },
  },
  -- from: https://akos.ma/blog/adopting-wezterm/
  hyperlink_rules = {
    -- Matches: a URL in parens: (URL)
    {
      regex = "\\((\\w+://\\S+)\\)",
      format = "$1",
      highlight = 1,
    },
    -- Matches: a URL in brackets: [URL]
    {
      regex = "\\[(\\w+://\\S+)\\]",
      format = "$1",
      highlight = 1,
    },
    -- Matches: a URL in curly braces: {URL}
    {
      regex = "\\{(\\w+://\\S+)\\}",
      format = "$1",
      highlight = 1,
    },
    -- Matches: a URL in angle brackets: <URL>
    {
      regex = "<(\\w+://\\S+)>",
      format = "$1",
      highlight = 1,
    },
    -- Then handle URLs not wrapped in brackets
    {
      -- Before
      --regex = '\\b\\w+://\\S+[)/a-zA-Z0-9-]+',
      --format = '$0',
      -- After
      regex = "[^(]\\b(\\w+://\\S+[)/a-zA-Z0-9-]+)",
      format = "$1",
      highlight = 1,
    },
    -- implicit mailto link
    {
      regex = "\\b\\w+@[\\w-]+(\\.[\\w-]+)+\\b",
      format = "mailto:$0",
    },
  },
}
return config
