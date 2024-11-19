import os
import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import socket
import psutil
import ctypes
import getpass
import requests
from io import BytesIO
import time
import winreg

#openweathermap.org api
WEATHER_API_KEY = "your_key"
WEATHER_CITY = "Vienna"
WEATHER_ICON_FOLDER = "C:/Python313/icons/"
WEATHER_LANG = "en"

def get_wallpaper_path():
    # Open the "Control Panel\Desktop" registry key
    reg_key = r"Control Panel\Desktop"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key)
        # Read the "Wallpaper" value
        wallpaper_path, _ = winreg.QueryValueEx(key, "WallPaper")
        winreg.CloseKey(key)
        return wallpaper_path
    except Exception as e:
        print(f"Error: {e}")
        return None
        
# Function to fetch weather data
def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={WEATHER_CITY}&units=metric&appid={WEATHER_API_KEY}&lang={WEATHER_LANG}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
        feelslike = data['main']['feels_like']
        wind = data['wind']['speed']
        icon_code = data['weather'][0]['icon']  # Get weather icon code
        
        print(data) 
        return f"{temperature}°C,", weather_description.capitalize(), icon_code, f"{feelslike}°C", f"{wind} meter/sec"
    else:
        print("Error Weather")        
        return "Weather data unavailable", None
        
def get_weather_icon(icon_code):
    """Check if the weather icon exists in the folder, otherwise download it from the URL."""
    os.makedirs(WEATHER_ICON_FOLDER, exist_ok=True)  # Ensure the folder exists
    local_icon_path = os.path.join(WEATHER_ICON_FOLDER, f"{icon_code}.png")
    
    # Check if the icon already exists
    if os.path.exists(local_icon_path):
        print("icon exists")
        return Image.open(local_icon_path)
    
    # If not, download the icon
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
    print("icon downloading")
    try:
        response = requests.get(icon_url)
        if response.status_code == 200:
            icon_image = Image.open(BytesIO(response.content))
            icon_image.save(local_icon_path)  # Save the downloaded icon locally
            return icon_image
    except Exception as e:
        print(f"Error fetching weather icon: {e}")
    
    return None
        
def update_wallpaper():
    # Retrieve user, device name, and IP address information
    username = getpass.getuser()
    hostname = socket.gethostname()
    
    wallpaper_path = get_wallpaper_path()

    # Specify the path of the folder containing images
    image_folder = os.path.dirname(wallpaper_path)
    image_filename = os.path.basename(wallpaper_path)
    backup_folder = os.path.join(image_folder, "backup/")

    os.makedirs(backup_folder, exist_ok=True)  # Ensure the backup folder exists
    
    # Create the backup file path
    backup_file_path = os.path.join(backup_folder, f"{image_filename}.backup.jpg")    

    # Check if a backup file exists
    if os.path.exists(backup_file_path):
        print(f"Backup file exists. Using backup file: {backup_file_path}")
        image_path = backup_file_path  # Use the backup file
    else:
        print("No backup file found. Creating a new backup.")
        # Copy the selected image to the backup folder
        image = Image.open(wallpaper_path)  # Open the original image
        image.save(backup_file_path)  # Save it as a backup

    # Load and process the image
    image = Image.open(backup_file_path)

    # Set the font for the text
    try:
        font = ImageFont.truetype("arial.ttf", 30)  # For Windows
        bold_font = ImageFont.truetype("arialbd.ttf", 30)  # Bold font
    except IOError:
        font = ImageFont.load_default()  # Use default font if arial.ttf is unavailable
        bold_font = font

    # Shadow and background settings
    blur_radius = 5  # Blur radius for shadow
    background_padding = 20  # Extra size for the background compared to text
    corner_radius = 15  # Roundness of corners
    table_padding = 10  # Padding around the table
    table_row_height = 40  # Height between rows

    # Retrieve IP addresses of network interfaces
    network_info = psutil.net_if_addrs()
    table_data = [("", ""), ("User :", username), ("Host :", hostname), ("", "")]  # Add username and hostname as the first two rows

    for iface, addrs in network_info.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:  # Only include IPv4 addresses
                iface_name = iface
                iface_ip = addr.address

                # Skip addresses starting with 169.254.x.x or 127.0.0.1
                if iface_ip.startswith("169.254") or iface_ip.startswith("127.0.0.1"):
                    continue

                table_data.append((iface_name, iface_ip))

    # Add the last update time to the table data
    last_update_time = f"{datetime.datetime.now().strftime('%H:%M:%S')}"
    today_date = f"{datetime.datetime.now().strftime('%Y-%m-%d')}"
    table_data.append(("", ""))
    table_data.append(("Update Time :", last_update_time))
    table_data.append(("", ""))
    table_data.append(("Date :", today_date))
    table_data.append(("", ""))

    # Fetch weather data
    weather_temp, weather_desc, weather_icon_code, weather_feels_like, weather_wind_speed = get_weather()
    table_data.append(("Weather Temp :", weather_temp))  # Add weather info to the table
    table_data.append(("Feels Like :", weather_feels_like))  # Add weather info to the table
    table_data.append(("Wind Speed :", weather_wind_speed))  # Add weather info to the table
    table_data.append(("Status :", weather_desc))  # Add weather info to the table
    table_data.append(("", ""))
    table_data.append(("", ""))    

    # Calculate table dimensions
    draw = ImageDraw.Draw(image)
    table_width = max([draw.textbbox((0, 0), f"{iface}: {ip}", font=font)[2] for iface, ip in table_data]) + 2 * table_padding
    table_height = len(table_data) * table_row_height + 2 * table_padding

    # Draw a rounded rectangle for the table background
    width, height = image.size
    table_background_rect = (
        width - table_width - 10,
        10,
        width - 10,
        table_height + 10 + (50 if weather_icon_code else 0)  # Add extra space for the icon
    )

    # Draw the background with a shadow
    shadow_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.rounded_rectangle(table_background_rect, fill="black", radius=corner_radius)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
    image = Image.alpha_composite(image.convert("RGBA"), shadow_layer)

    # Add table text to the top-right corner
    table_y_offset = table_background_rect[1] + table_padding
    for iface_name, iface_ip in table_data:
        table_text_left = iface_name
        table_text_right = iface_ip

        draw = ImageDraw.Draw(image)
        draw.text((table_background_rect[0] + table_padding, table_y_offset), table_text_left, font=font, fill="white")

        # Calculate text dimensions using textbbox()
        text_bbox = draw.textbbox((0, 0), table_text_right, font=bold_font)
        text_width = text_bbox[2] - text_bbox[0]

        # Position for right-aligned text
        draw.text((width - table_padding - text_width, table_y_offset), table_text_right, font=bold_font, fill="yellow")  # Bold yellow text
        table_y_offset += table_row_height

    # Add weather icon to the bottom of the table
    if weather_icon_code:
        icon_image = get_weather_icon(weather_icon_code)
        
        # Resize the icon
        icon_size = (150, 150)
        icon_image = icon_image.resize(icon_size, Image.Resampling.LANCZOS)
        icon_image = icon_image.convert("RGBA")
        
        icon_x = width - table_width - 20
        icon_y = table_y_offset - 80 
        
        # Add a highlight effect for the icon
        highlight_layer = Image.new("RGBA", icon_size, (255, 255, 255, 0))
        highlight_draw = ImageDraw.Draw(highlight_layer)
        highlight_draw.ellipse(
            [10, 10, icon_size[0] - 10, icon_size[1] - 10],
            fill=(255, 255, 255, 100)
        )
        image.paste(highlight_layer, (icon_x, icon_y), highlight_layer)

        # Add shadow for the icon
        shadow_icon = icon_image.copy().convert("RGBA")
        shadow_icon = shadow_icon.filter(ImageFilter.GaussianBlur(10))
        shadow_position = (icon_x + 5, icon_y + 5)
        image.paste(shadow_icon, shadow_position, shadow_icon)

        # Paste the icon on its original position
        image.paste(icon_image, (icon_x, icon_y), icon_image)

    # Save the updated image as the new wallpaper
    new_wallpaper_path = os.path.join(image_folder, wallpaper_path)
    image.convert("RGB").save(new_wallpaper_path)
    print(f"New wallpaper saved at '{new_wallpaper_path}'.")

    # Set the new wallpaper as the desktop background
    ctypes.windll.user32.SystemParametersInfoW(20, 260, new_wallpaper_path, 0)
    print("New wallpaper set as the desktop background.")

# Run the update process in a loop
while True:
    update_wallpaper()
    time.sleep(10)  # Wait for 10 seconds before updating again
