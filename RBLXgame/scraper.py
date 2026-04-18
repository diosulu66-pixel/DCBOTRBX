import requests
import xml.etree.ElementTree as ET
import os

session = requests.Session()

def get_asset_location(asset_id):
    url = f"https://assetdelivery.roblox.com/v1/assetId/{asset_id}"
    try:
        response = session.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('location')
        else:
            return None
    except Exception as e:
        print(f"Error requesting asset: {e}")
        return None

def extract_texture_id(xml_content):
    try:
        root = ET.fromstring(xml_content)
        for elem in root.iter():
            if elem.tag == 'url':
                url_text = elem.text
                if 'id=' in url_text:
                    texture_id = int(url_text.split('=')[1])
                    return texture_id
    except ET.ParseError:
        print("Error parsing XML for asset")
    return None

async def get_clothing_template(asset_id: int):
    """
    Función adaptada para Discord.
    Retorna (bytes_de_la_imagen, mensaje_de_error)
    """
    # Leer la cookie directamente de las variables de entorno
    cookie_val = os.getenv('ROBLOX_COOKIE')
    if not cookie_val:
        return None, "El bot no tiene configurada la variable de entorno `ROBLOX_COOKIE` en el servidor."
    
    session.cookies.set('.ROBLOSECURITY', cookie_val, domain='.roblox.com')

    # 1. Obtener la data del asset original (puede ser XML o PNG directo)
    asset_url = get_asset_location(asset_id)
    if not asset_url:
        return None, f"No se pudo encontrar la ubicación del asset ID {asset_id}. ¿Es privado o inválido?"

    try:
        response = requests.get(asset_url)
        if response.status_code != 200:
            return None, f"Error descargando el asset original (Status {response.status_code})"

        content = response.text

        # 2. Si es un archivo XML, necesitamos extraer la textura real
        if content.startswith('<roblox'):
            texture_id = extract_texture_id(content)
            if not texture_id:
                return None, "Se encontró el asset pero no se pudo extraer el ID de la textura interna."

            # Obtener URL de la textura real
            texture_url = get_asset_location(texture_id)
            if not texture_url:
                return None, f"No se pudo obtener la URL de la textura real (ID: {texture_id})."

            img_response = requests.get(texture_url)
            if img_response.status_code == 200:
                return img_response.content, None  # Retornar los bytes directamente
            else:
                return None, f"Error descargando la imagen de la textura final (Status {img_response.status_code})"
        else:
            # Si no es XML, es probable que ya sea la imagen directa (png)
            return response.content, None
            
    except Exception as e:
        return None, f"Excepción interna: {str(e)}"
