-- Omarchy Floating Controls: mouse controls to Omarchy's floating titlebars.
local titlebars = "/usr/lib/omarchy-hyprland-titlebars/titlebars.so"
local mode = "both"
local settings = io.open(os.getenv("HOME") .. "/.local/share/omarchy-floating-controls/settings.json", "r")
if settings then
  local value = (settings:read(1024) or ""):match('"mode"%s*:%s*"([a-z]+)"')
  settings:close()
  if value == "workspace" or value == "halves" or value == "none" then mode = value end
end
local old_load = hl.plugin.load
hl.plugin.load = function(path, ...)
  local result = old_load(path, ...)
  if mode ~= "none" and path == titlebars and hl.plugin.hyprbars and not hl.plugin.hyprbars.__floating_controls then
    local bars = hl.plugin.hyprbars
    local add = bars.add_button
    bars.add_button = function(button)
      if button.icon == "□" and mode ~= "workspace" then
        local helper = os.getenv("HOME") .. "/.local/share/omarchy-floating-controls/bin/floating-controls-half"
        add({ bg_color = button.bg_color, fg_color = button.fg_color, size = button.size, icon = "◧", action = "'" .. helper .. "' %WINDOW% right" })
        add(button)
        return add({ bg_color = button.bg_color, fg_color = button.fg_color, size = button.size, icon = "◨", action = "'" .. helper .. "' %WINDOW% left" })
      end
      if button.icon == "−" and mode ~= "halves" then
        local helper = os.getenv("HOME") .. "/.local/share/omarchy-floating-controls/bin/floating-controls-workspace"
        add(button)
        add({ bg_color = button.bg_color, fg_color = button.fg_color, size = button.size, icon = "▶", action = "'" .. helper .. "' %WINDOW% next" })
        return add({ bg_color = button.bg_color, fg_color = button.fg_color, size = button.size, icon = "◀", action = "'" .. helper .. "' %WINDOW% prev" })
      end
      return add(button)
    end
    bars.__floating_controls = true
  end
  return result
end
