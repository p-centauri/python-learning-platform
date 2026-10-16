-- Supplied Redis 7.4 guard: one explicit ID, at most eight current groups.
-- XINFO allocates all group metadata before the eight-group check: trusted topology only.
-- Freeze group creation/destruction/SETID separately. This does not protect future groups.
local rows = redis.call('XRANGE', KEYS[1], ARGV[1], ARGV[1], 'COUNT', 1)
if #rows == 0 then return 'missing' end
local fields = rows[1][2]
if #fields ~= 2 or fields[1] ~= 'payload' or fields[2] ~= ARGV[2] then return 'blocked' end
local groups = redis.call('XINFO', 'GROUPS', KEYS[1])
if #groups == 0 or #groups > 8 then return 'blocked' end
-- Compare unsigned decimal components as strings, avoiding Lua float precision loss.
local function normalize(s)
    local v = string.gsub(s, '^0+', '')
    if v == '' then return '0' end
    return v
end
local function less(a, b)
    a, b = normalize(a), normalize(b)
    if #a ~= #b then return #a < #b end
    return a < b
end
local function before(a, b)
    local am, as = string.match(a, '^(%d+)%-(%d+)$')
    local bm, bs = string.match(b, '^(%d+)%-(%d+)$')
    return less(am, bm) or (normalize(am) == normalize(bm) and less(as, bs))
end
for _, group in ipairs(groups) do
    local name, last
    for i = 1, #group, 2 do
        if group[i] == 'name' then name = group[i+1] end
        if group[i] == 'last-delivered-id' then last = group[i+1] end
    end
    if not name or not last or before(last, ARGV[1]) then return 'blocked' end
    if #redis.call('XPENDING', KEYS[1], name, ARGV[1], ARGV[1], 1) > 0 then return 'blocked' end
end
if redis.call('XDEL', KEYS[1], ARGV[1]) == 1 then return 'removed' end
return 'missing'

