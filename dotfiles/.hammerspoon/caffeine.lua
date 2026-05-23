-- "handrolled" caffeine from the hammerspoon Getting Started doc
caffeine = hs.menubar.new()
function setCaffeineDisplay(state)
    if state then
        caffeine:setTitle("☕️")
    else
        caffeine:setTitle("😴")
    end
end

function caffeineClicked()
    setCaffeineDisplay(hs.caffeinate.toggle("displayIdle"))
end

if caffeine then
    caffeine:setClickCallback(caffeineClicked)
    setCaffeineDisplay(hs.caffeinate.get("displayIdle"))
end

hs.hotkey.bind({"cmd", "alt", "ctrl"}, "C", function ()
  state = hs.caffeinate.toggle("displayIdle")

  if state then
    hs.alert.show("Caffeine: ON")
  else
    hs.alert.show("Caffeine: OFF")
  end

  setCaffeineDisplay(state)
end)