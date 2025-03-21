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
import json

try:
    # settings.json file loading
    with open("settings.json", "r") as file:
        settings = json.load(file)

    # Use settings.json file vaules
    UPDATE_TIME = settings["APP"]["UPDATE_TIME"]
    DOWNLOAD_BING = settings["APP"]["DOWNLOAD_BING"]
    WALLPAPER_FOLDER = settings["APP"]["WALLPAPER_FOLDER"]
    
    WEATHER_API_KEY = settings["WEATHER"]["WEATHER_API_KEY"]
    WEATHER_CITY = settings["WEATHER"]["WEATHER_CITY"]
    WEATHER_CUSTOM_ICO = settings["WEATHER"]["WEATHER_CUSTOM_ICO"]
    WEATHER_ICON_FOLDER = settings["WEATHER"]["WEATHER_ICON_FOLDER"]
    WEATHER_ICON_SHADOW = settings["WEATHER"]["WEATHER_ICON_SHADOW"]
    WEATHER_ICON_HIGHLIGHT = settings["WEATHER"]["WEATHER_ICON_HIGHLIGHT"]
    WEATHER_ICON_SIZE = settings["WEATHER"]["WEATHER_ICON_SIZE"]
    WEATHER_LANG = settings["WEATHER"]["WEATHER_LANG"]

    INFO_USER = settings["INFO"]["INFO_USER"]
    INFO_HOST = settings["INFO"]["INFO_HOST"]
    INFO_TIME = settings["INFO"]["INFO_TIME"]
    INFO_DATE = settings["INFO"]["INFO_DATE"]
    INFO_LANS = settings["INFO"]["INFO_LANS"]
    INFO_CPU = settings["INFO"]["INFO_CPU"]
    INFO_RAM = settings["INFO"]["INFO_RAM"]

    blur_radius = settings["TABLE_SETTINGS"]["BLUR_RADIUS"]
    background_padding = settings["TABLE_SETTINGS"]["BACKGROUND_PADDING"]
    corner_radius = settings["TABLE_SETTINGS"]["CORNER_RADIUS"]
    table_padding = settings["TABLE_SETTINGS"]["TABLE_PADDING"]
    table_row_height = settings["TABLE_SETTINGS"]["TABLE_ROW_HEIGHT"]
    background_opacity = settings["TABLE_SETTINGS"]["BACKGROUND_OPACITY"]


    print(f"WEATHER_API_KEY: {WEATHER_API_KEY}")
    print(f"WEATHER_CITY: {WEATHER_CITY}")
    print(f"UPDATE_TIME: {UPDATE_TIME}")
    
except Exception as e:
        print(f"Error settings: {e}")
        
import requests
import os

def download_bing_wallpaper():
    save_folder = WALLPAPER_FOLDER
    """
    Downloads Bing's daily wallpaper.
    Skips downloading if the file already exists.

    :param save_folder: The folder where images will be saved.
    """
    os.makedirs(save_folder, exist_ok=True)

    # Fetch JSON data from Bing API
    bing_api = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US"
    response = requests.get(bing_api)
    
    if response.status_code != 200:
        print("Failed to access Bing API.")
        return
    
    data = response.json()
    
    # Extract image details
    image = data["images"][0]
    image_url = "https://www.bing.com" + image["urlbase"] + "_UHD.jpg"
    image_date = image["fullstartdate"]  # Example: "20240317"

    # Create the file name
    file_name = f"{image_date}.jpg"
    file_path = os.path.join(save_folder, file_name)

    # Check if the file already exists
    if os.path.exists(file_path):
        print(f"Image already exists: {file_name}")
        return file_name

    # Download and save the image
    image_response = requests.get(image_url)
    if image_response.status_code == 200:
        with open(file_path, "wb") as file:
            file.write(image_response.content)
        print(f"New wallpaper downloaded: {file_name}")
        return file_name
    else:
        print("Failed to download the image.")
        return ""
        

def get_wallpaper_path():
    try:        
        reg_key = r"Control Panel\Desktop"    
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key)        
        wallpaper_path, _ = winreg.QueryValueEx(key, "WallPaper")
        winreg.CloseKey(key)
        return wallpaper_path
    except Exception as e:
        print(f"Error: {e}")
        return None
        
# Function to fetch weather data
def get_weather(table_data):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={WEATHER_CITY}&units=metric&appid={WEATHER_API_KEY}&lang={WEATHER_LANG}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            weather_desc = data['weather'][0]['description']
            weather_temp = data['main']['temp']
            weather_feels_like = data['main']['feels_like']
            weather_wind_speed = data['wind']['speed']
            weather_icon_code = data['weather'][0]['icon']  # Get weather icon code
            
            print(f"{weather_temp}°C,", weather_desc.capitalize(), weather_icon_code, f"{weather_feels_like}°C", f"{weather_wind_speed} mt/s")
            
            table_data.append(("", ""))
            
            table_data.append(("Weather Temp :", f"{weather_temp} °C"))  # Add weather info to the table
            table_data.append(("Feels Like :", f"{weather_feels_like} °C"))  # Add weather info to the table
            table_data.append(("Wind Speed :", f"{weather_wind_speed} mt/s"))  # Add weather info to the table
            table_data.append(("Status :", weather_desc.capitalize()))  # Add weather info to the table
            table_data.append(("", ""))
            table_data.append(("", ""))
            return weather_icon_code
        else:
            print("Error Weather")
            table_data.append(("Weather", "Error"))
            return ""
    except Exception as e:
        print(f"Error fetching weather icon: {e}")    
        return None    
        
def get_weather_icon(icon_code):
    try:
        print(f"icon code={icon_code}")

        #Check if the weather icon exists in the folder, otherwise download it from the URL.
        icons_folder = os.path.dirname(os.path.abspath(__file__))
        icons_folder = os.path.join(icons_folder, WEATHER_ICON_FOLDER)

        os.makedirs(icons_folder, exist_ok=True)  # Ensure the folder exists
        local_icon_path = os.path.join(icons_folder, f"{icon_code}.png")
        
        # Check if the icon already exists
        if WEATHER_CUSTOM_ICO:
            print(f"icon path{local_icon_path}")
            if os.path.exists(local_icon_path):
                print("icon exists")
                return Image.open(local_icon_path)
            
        # If not, download the icon
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        print("icon downloading")
    
        response = requests.get(icon_url)
        if response.status_code == 200:
            icon_image = Image.open(BytesIO(response.content))            
            return icon_image
    except Exception as e:
        print(f"Error fetching weather icon: {e}")    
        return None
    
def get_pc_info(table_data):
    try:
        if INFO_USER:
            username = getpass.getuser()    
            table_data.append(("User :", username))
        
        if INFO_HOST:
            hostname = socket.gethostname()
            table_data.append(("Host :", hostname))     
    except Exception as e:
        print(f"Error get_pc_info: {e}")
    
def get_cpu_infos(table_data):
    try:
        if INFO_CPU:
            table_data.append(("", ""))

            logical_cores = psutil.cpu_count(logical=True)
            physical_cores = psutil.cpu_count(logical=False)
            cpu_frequency = psutil.cpu_freq()

            # Make the frequency readable
            cpu_freq_str = f"{cpu_frequency.current:.2f} MHz"

            table_data.append(("CPU Cores :", f"{logical_cores} L / {physical_cores} P"))
            table_data.append(("CPU Freq :", cpu_freq_str))
    except Exception as e:
        print(f"Error get_cpu_infos: {e}")

def get_ram_infos(table_data):
    try:
        if INFO_RAM:
            table_data.append(("", ""))

            virtual_memory = psutil.virtual_memory()
            print("RAM Information:")
            print(f"  Total Memory: {virtual_memory.total / (1024 ** 3):.2f} GB")
            print(f"  Available Memory: {virtual_memory.available / (1024 ** 3):.2f} GB")
            print(f"  Used Memory: {virtual_memory.used / (1024 ** 3):.2f} GB")
            print(f"  Free Memory: {virtual_memory.free / (1024 ** 3):.2f} GB")
            print(f"  Memory Usage Percentage: {virtual_memory.percent}%")
            
            # swap_memory = psutil.swap_memory()
            # print("\nSwap Memory Information:")
            # print(f"  Total Swap: {swap_memory.total / (1024 ** 3):.2f} GB")
            # print(f"  Used Swap: {swap_memory.used / (1024 ** 3):.2f} GB")
            # print(f"  Free Swap: {swap_memory.free / (1024 ** 3):.2f} GB")
            # print(f"  Swap Usage Percentage: {swap_memory.percent}%")
            
            table_data.append(("Total Ram :", f"{virtual_memory.total / (1024 ** 3):.2f} GB"))
            table_data.append(("Used Ram :", f"{virtual_memory.used / (1024 ** 3):.2f} GB"))
            table_data.append(("Used % :", f"{virtual_memory.percent}%"))
    except Exception as e:
        print(f"Error get_ram_infos: {e}")
       
def get_network_infos(table_data):
    try:
        if INFO_LANS:
            table_data.append(("", ""))

            # Retrieve IP addresses of network interfaces
            network_info = psutil.net_if_addrs()
            for iface, addrs in network_info.items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # Only include IPv4 addresses
                        iface_name = iface
                        iface_ip = addr.address

                        # Skip addresses starting with 169.254.x.x or 127.0.0.1
                        if iface_ip.startswith("169.254") or iface_ip.startswith("127.0.0.1"):
                            continue

                        table_data.append((iface_name, iface_ip))
    except Exception as e:
        print(f"Error get_network_infos: {e}")
                    
def get_date_time(table_data):    
    try:
        if INFO_TIME:
            last_update_time = f"{datetime.datetime.now().strftime('%H:%M:%S')}"        
            table_data.append(("", ""))
            table_data.append(("Update Time :", last_update_time))
            
        if INFO_DATE:
            today_date = f"{datetime.datetime.now().strftime('%Y-%m-%d')}"
            table_data.append(("", ""))
            table_data.append(("Date :", today_date))
    except Exception as e:
        print(f"Error get_date_time: {e}")
        
def backup_wallpaper(wallpaper_path):
    try:
        # Specify the path of the folder containing images
        image_folder = os.path.dirname(wallpaper_path)
        image_filename = os.path.basename(wallpaper_path)
        backup_folder = os.path.join(image_folder, "backup\\")

        os.makedirs(backup_folder, exist_ok=True)  # Ensure the backup folder exists
        
        # Create the backup file path
        backup_file_path = os.path.join(backup_folder, f"{image_filename}")    

        # Check if a backup file exists
        if os.path.exists(backup_file_path):
            print(f"Backup file exists. Using backup file: {backup_file_path}")
            image_path = backup_file_path  # Use the backup file
        else:
            print("No backup file found. Creating a new backup.")
            # Copy the selected image to the backup folder
            image = Image.open(wallpaper_path)  # Open the original image
            image.save(backup_file_path)  # Save it as a backup
            
        return backup_file_path
    except Exception as e:
        print(f"Error backup_wallpaper: {e}")
        return None
    
def add_weather_icon(image, weather_icon_code, width, table_width, table_y_offset):
    try:
        if weather_icon_code:
            print (f"icon code{weather_icon_code}")
            icon_image = get_weather_icon(weather_icon_code)
            
            # Resize the icon        
            new_width = WEATHER_ICON_SIZE
            aspect_ratio = new_width / icon_image.width
            new_height = int(icon_image.height * aspect_ratio)
            icon_size = (new_width, new_height)        
            icon_image = icon_image.resize(icon_size, Image.Resampling.LANCZOS)
            icon_image = icon_image.convert("RGBA")
            
            icon_x = width - (table_width+new_width)//2 
            icon_y = table_y_offset - 80 
            
            # Add a highlight effect for the icon
            if(WEATHER_ICON_HIGHLIGHT):
                highlight_layer = Image.new("RGBA", icon_size, (255, 255, 255, 0))
                highlight_draw = ImageDraw.Draw(highlight_layer)
                highlight_draw.ellipse(
                    [10, 10, icon_size[0] - 10, icon_size[1] - 10],
                    fill=(255, 255, 255, 100)
                )
                image.paste(highlight_layer, (icon_x, icon_y), highlight_layer)

            # Add shadow for the icon
            if(WEATHER_ICON_SHADOW):            
                shadow_icon = icon_image.copy().convert("RGBA")
                shadow_icon = shadow_icon.filter(ImageFilter.GaussianBlur(10))
                shadow_position = (icon_x + 5, icon_y + 5)
                image.paste(shadow_icon, shadow_position, shadow_icon)

            # Paste the icon on its original position
            image.paste(icon_image, (icon_x, icon_y), icon_image)
    except Exception as e:
        print(f"Error add_weather_icon: {e}")
        
def update_wallpaper():   
    try:
        wallpaper_path = ""
        image_folder = ""        
        backup_file_path = ""
        
        if(DOWNLOAD_BING):
            bing_image = download_bing_wallpaper()
            wallpaper_path =  os.getcwd() + "\\" + os.path.join(WALLPAPER_FOLDER, bing_image)
            image_folder = os.path.dirname(wallpaper_path)        
            backup_file_path = backup_wallpaper(wallpaper_path)            
        else:
            wallpaper_path = get_wallpaper_path()            
            image_folder = os.path.dirname(wallpaper_path)        
            backup_file_path = backup_wallpaper(wallpaper_path)    
        
        print(wallpaper_path)
        print(image_folder)
        print(backup_file_path)
        # Load and process the image
        image = Image.open(backup_file_path)

        # Set the font for the text
        try:
            font = ImageFont.truetype("arial.ttf", 30)  # For Windows
            bold_font = ImageFont.truetype("arialbd.ttf", 30)  # Bold font
        except IOError:
            font = ImageFont.load_default()  # Use default font if arial.ttf is unavailable
            bold_font = font
        
        table_data = [("", "")]
        
        get_pc_info(table_data)
        
        get_cpu_infos(table_data)
        
        get_network_infos(table_data)
        
        get_ram_infos(table_data)
        
        get_date_time(table_data)
        
        weather_icon_code = get_weather(table_data)
        
        # Calculate table dimensions
        draw = ImageDraw.Draw(image)
        # Calculate the maximum width of text in the table
        table_width = max(draw.textbbox((0, 0), f"{name}: {value}", font=font)[2] for name, value in table_data) + 2 * table_padding
        # Calculate the total height of the table
        table_height = len(table_data) * table_row_height + 2 * table_padding

        # Draw a rounded rectangle for the table background
        width, height = image.size
        table_background_rect = (
            width - table_width - 10,
            10,
            width - 10,
            table_height + 10 + (50 if weather_icon_code else 0)  # Add extra space for the icon
        )

        # Black background color with transparency
        background_color = (0, 0, 0, background_opacity)

        # Draw the background with transparency
        shadow_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.rounded_rectangle(table_background_rect, fill=background_color, radius=corner_radius)
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
        image = Image.alpha_composite(image.convert("RGBA"), shadow_layer)

        # Add table text to the top-right corner
        table_y_offset = table_background_rect[1] + table_padding
        for data_name, data_value in table_data:
            table_text_left = str(data_name)  # Convert iface_name to string
            table_text_right = str(data_value)  # Convert iface_ip to string

            draw = ImageDraw.Draw(image)
            draw.text((table_background_rect[0] + table_padding, table_y_offset), table_text_left, font=font, fill="white")

            # Calculate text dimensions using textbbox()
            text_bbox = draw.textbbox((0, 0), table_text_right, font=bold_font)
            text_width = text_bbox[2] - text_bbox[0]

            # Position for right-aligned text
            draw.text((width - table_padding - text_width, table_y_offset), table_text_right, font=bold_font, fill="yellow")  # Bold yellow text
            table_y_offset += table_row_height

        # Add weather icon to the bottom of the table
        add_weather_icon(image, weather_icon_code, width, table_width, table_y_offset)    

        # Save the updated image as the new wallpaper
        new_wallpaper_path = os.path.join(image_folder, wallpaper_path)
        image.convert("RGB").save(new_wallpaper_path)
        print(f"New wallpaper saved at '{new_wallpaper_path}'.")

        # Set the new wallpaper as the desktop background
        ctypes.windll.user32.SystemParametersInfoW(20, 260, new_wallpaper_path, 0)
        print("New wallpaper set as the desktop background.")
    except Exception as e:
        print(f"Error update_wallpaper: {e}")

# Run the update process in a loop
while True:
    try:
        update_wallpaper()
        time.sleep(int(UPDATE_TIME))  # Wait for 10 seconds before updating again
    except Exception as e:
        print(f"Error in main loop: {e}")
