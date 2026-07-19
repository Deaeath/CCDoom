-- debug_flash.lua: one-off diagnostic, prints real numbers instead of guessing
-- from screenshots. Run with: debug_flash
local scriptDir = fs.getDir(shell.getRunningProgram())
local w, h = term.getSize()
print("term size: " .. w .. "x" .. h)
print("script dir: " .. scriptDir)

local function measure(path)
    local full = fs.combine(scriptDir, path)
    local img = paintutils.loadImage(full)
    if not img then
        print("FAILED to load: " .. full)
        return 0, 0
    end
    local iw, ih = 0, 0
    for y, row in pairs(img) do
        if y > ih then ih = y end
        for x in pairs(row) do
            if x > iw then iw = x end
        end
    end
    return iw, ih
end

local fireW, fireH = measure("images/fire")
local bfireW, bfireH = measure("images/bfire")
local gunW, gunH = measure("images/gun")
local bgunW, bgunH = measure("images/bgun")

print("fire: " .. fireW .. "x" .. fireH)
print("bfire: " .. bfireW .. "x" .. bfireH)
print("gun: " .. gunW .. "x" .. gunH)
print("bgun: " .. bgunW .. "x" .. bgunH)

print("computed fireX (normal): " .. math.floor((w - fireW) / 2 + 0.5))
print("computed fireX (blittle): " .. math.floor((w - bfireW) / 2 + 0.5))
