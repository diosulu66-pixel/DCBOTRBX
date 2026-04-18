local ReplicatedStorage = game:GetService("ReplicatedStorage")
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ProductFetcher = require(script.Parent:WaitForChild("ProductFetcher"))

local DonationEvents = ReplicatedStorage:WaitForChild("DonationEvents")
local ClaimStandEvent = DonationEvents:WaitForChild("ClaimStand")
local PromptPurchaseEvent = DonationEvents:WaitForChild("PromptPurchase")

-- Tabla para rastrear qué jugador posee qué stand
local Stands = {}

-- Función para reclamar un stand
ClaimStandEvent.OnServerInvoke = function(player, standModel)
	if not standModel then return false, "Stand no válido" end
	
	-- Comprobar si el jugador ya tiene un stand
	for _, ownerId in pairs(Stands) do
		if ownerId == player.UserId then
			return false, "Ya posees un stand."
		end
	end
	
	-- Comprobar si el stand ya está reclamado
	if Stands[standModel] then
		return false, "Este stand ya está reclamado."
	end
	
	-- Reclamar
	Stands[standModel] = player.UserId
	
	-- Cambiar título del stand (asumiendo que tiene un texto en 'Board.SurfaceGui.TextLabel')
	local board = standModel:FindFirstChild("Board")
	if board and board:FindFirstChild("SurfaceGui") and board.SurfaceGui:FindFirstChild("TextLabel") then
		board.SurfaceGui.TextLabel.Text = "Stand de " .. player.Name
	end
	
	-- Obtener los pases de juego del jugador
	local passes = ProductFetcher.GetUserGamePasses(player.UserId)
	
	-- Actualizar la UI del stand con los pases
	-- Aquí normalmente iterarías sobre un BillboardGui o SurfaceGui en el stand para crear botones
	-- Simularemos el envío de esta información de vuelta al cliente
	return true, passes
end

-- Limpiar el stand si el jugador se desconecta
Players.PlayerRemoving:Connect(function(player)
	for standModel, ownerId in pairs(Stands) do
		if ownerId == player.UserId then
			Stands[standModel] = nil
			local board = standModel:FindFirstChild("Board")
			if board and board:FindFirstChild("SurfaceGui") and board.SurfaceGui:FindFirstChild("TextLabel") then
				board.SurfaceGui.TextLabel.Text = "Stand Libre"
			end
			-- Limpiar botones del stand (esto dependerá de la estructura de tu modelo)
		end
	end
end)

-- Cuando un jugador intenta comprar un pase desde un stand
PromptPurchaseEvent.OnServerEvent:Connect(function(buyer, gamePassId)
	if type(gamePassId) == "number" then
		MarketplaceService:PromptGamePassPurchase(buyer, gamePassId)
	end
end)

-- IMPORTANTE: Procesar compras
-- Aunque MarketplaceService procesa Game Passes de forma automática, si usamos Developer Products necesitamos ProcessReceipt
-- Para donaciones, normalmente son Game Passes o Developer Products de terceros.
-- Para que el creador gane robux de pases de otros juegos, debe estar habilitada la opción "Allow Third Party Sales" en los ajustes del juego.

MarketplaceService.PromptGamePassPurchaseFinished:Connect(function(player, gamePassId, wasPurchased)
	if wasPurchased then
		print(player.Name .. " ha comprado el pase " .. tostring(gamePassId))
		-- Aquí podrías añadir un efecto de donación, actualizar un leaderboard de donaciones, etc.
	end
end)
