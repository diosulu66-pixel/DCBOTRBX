local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local player = Players.LocalPlayer
local DonationEvents = ReplicatedStorage:WaitForChild("DonationEvents")
local ClaimStandEvent = DonationEvents:WaitForChild("ClaimStand")
local PromptPurchaseEvent = DonationEvents:WaitForChild("PromptPurchase")

-- Supongamos que todos los stands están en Workspace.Stands
local standsFolder = workspace:WaitForChild("Stands", 5)

if standsFolder then
	for _, stand in ipairs(standsFolder:GetChildren()) do
		local claimPart = stand:FindFirstChild("ClaimPart")
		if claimPart then
			local clickDetector = Instance.new("ClickDetector")
			clickDetector.Parent = claimPart
			
			clickDetector.MouseClick:Connect(function()
				local success, result = ClaimStandEvent:InvokeServer(stand)
				
				if success then
					print("Stand reclamado con éxito.")
					local passes = result
					
					-- Generar botones en el stand del jugador con sus pases
					local board = stand:FindFirstChild("Board")
					if board and board:FindFirstChild("SurfaceGui") and board.SurfaceGui:FindFirstChild("ItemsContainer") then
						-- Limpiar previos
						for _, child in ipairs(board.SurfaceGui.ItemsContainer:GetChildren()) do
							if child:IsA("TextButton") then child:Destroy() end
						end
						
						-- Crear nuevos botones para cada pase
						for i, passData in ipairs(passes) do
							local btn = Instance.new("TextButton")
							btn.Name = "Pass_" .. passData.id
							btn.Text = passData.name .. "\n$" .. passData.price
							btn.Size = UDim2.new(0, 100, 0, 50)
							btn.BackgroundColor3 = Color3.fromRGB(0, 255, 0)
							btn.Parent = board.SurfaceGui.ItemsContainer
							
							-- Añadir evento de compra para que OTROS jugadores puedan comprar
							-- Como este script corre en el cliente del que reclamó, 
							-- lo ideal es que otro script en StarterPlayer detecte clics en botones del SurfaceGui
						end
					end
				else
					warn("No se pudo reclamar: " .. tostring(result))
				end
			end)
		end
	end
end

-- Detectar clics en cualquier botón de donación de los stands
-- Esto asume que tienes botones en SurfaceGuis dentro del modelo del stand
local UserInputService = game:GetService("UserInputService")

local function onInputBegan(input, gameProcessed)
	if input.UserInputType == Enum.UserInputType.MouseButton1 then
		local mouse = player:GetMouse()
		local target = mouse.Target
		
		-- Comprobar si hicimos clic en un botón de un stand que representa un pase
		if target and target:IsA("BasePart") and target.Parent and target.Parent.Name == "Stand" then
			-- Esta lógica depende de cómo armes el GUI de donación en tu stand.
			-- Por ejemplo, si los botones tienen el GamePassId guardado en un atributo
			local passId = target:GetAttribute("GamePassId")
			if passId then
				PromptPurchaseEvent:FireServer(passId)
			end
		end
	end
end

UserInputService.InputBegan:Connect(onInputBegan)
