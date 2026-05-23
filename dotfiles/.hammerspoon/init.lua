-- watches config changes and reloads automatically
hs.loadSpoon("ReloadConfiguration")
spoon.ReloadConfiguration:start()

dofile('./app-shortcuts.lua')
dofile('./caffeine.lua')
dofile('./f-key-mode-toggle.lua')
dofile('./kid-lock.lua')
dofile('./pomodoro.lua')

-- claudeModel = dofile('./claude-model-display.lua')
-- claudeModel.start()
