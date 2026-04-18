local HttpService = game:GetService("HttpService")

local ProductFetcher = {}

-- Función para obtener los pases de juego de un jugador usando la API de Roblox (mediante un proxy público como roproxy)
function ProductFetcher.GetUserGamePasses(userId)
	local passes = {}
	
	-- 1. Obtener los juegos (universes) creados por el jugador
	local gamesUrl = "https://games.roproxy.com/v2/users/" .. tostring(userId) .. "/games?accessFilter=Public&sortOrder=Asc&limit=50"
	local success, result = pcall(function()
		return HttpService:GetAsync(gamesUrl)
	end)
	
	if not success then
		warn("Error al obtener juegos del usuario " .. tostring(userId) .. ":", result)
		return passes
	end
	
	local gamesData = HttpService:JSONDecode(result)
	
	if gamesData and gamesData.data then
		for _, gameData in ipairs(gamesData.data) do
			local universeId = gameData.id
			
			-- 2. Obtener los Game Passes de cada juego
			local passesUrl = "https://games.roproxy.com/v1/games/" .. tostring(universeId) .. "/game-passes?limit=100&sortOrder=Asc"
			local passSuccess, passResult = pcall(function()
				return HttpService:GetAsync(passesUrl)
			end)
			
			if passSuccess then
				local passData = HttpService:JSONDecode(passResult)
				if passData and passData.data then
					for _, pass in ipairs(passData.data) do
						table.insert(passes, {
							id = pass.id,
							name = pass.name,
							price = pass.price or 0,
							icon = "rbxassetid://" .. tostring(pass.iconImageAssetId)
						})
					end
				end
			end
			
			-- Pequeño delay para no saturar los límites de la API HTTP de Roblox
			task.wait(0.1)
		end
	end
	
	-- Ordenar pases por precio de menor a mayor
	table.sort(passes, function(a, b)
		return a.price < b.price
	end)
	
	return passes
end

return ProductFetcher
