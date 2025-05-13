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
import random
import sys # Added for sys.exit

class AppConfig:
    """
    Manages application configuration by loading settings from a JSON file.
    Handles file loading, parsing, and validation of required settings.
    """
    def __init__(self, settings_file_name="settings.json"):
        self.settings_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), settings_file_name)
        
        try:
            with open(self.settings_file_path, "r") as file:
                settings = json.load(file)
        except FileNotFoundError:
            print(f"Error: Configuration file '{self.settings_file_path}' not found. Please ensure it exists.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Configuration file '{self.settings_file_path}' is not a valid JSON file.")
            sys.exit(1)

        try:
            # APP settings
            app_s = settings["APP"]
            self.UPDATE_TIME = int(app_s["UPDATE_TIME"])
            self.DOWNLOAD_BING = bool(app_s["DOWNLOAD_BING"])
            self.DOWNLOAD_NASA = bool(app_s["DOWNLOAD_NASA"])
            self.DOWNLOAD_NASA_API = str(app_s["DOWNLOAD_NASA_API"])
            self.DOWNLOAD_PIXABAY = bool(app_s["DOWNLOAD_PIXABAY"])
            self.DOWNLOAD_PIXABAY_API = str(app_s["DOWNLOAD_PIXABAY_API"])
            self.DOWNLOAD_PIXABAY_CAT = str(app_s["DOWNLOAD_PIXABAY_CAT"])
            self.DOWNLOAD_PEXELS = bool(app_s["DOWNLOAD_PEXELS"])
            self.DOWNLOAD_PEXELS_API = str(app_s["DOWNLOAD_PEXELS_API"])
            self.DOWNLOAD_PEXELS_CAT = str(app_s["DOWNLOAD_PEXELS_CAT"])
            self.WALLPAPER_FOLDER = str(app_s["WALLPAPER_FOLDER"])
            self.WALLPAPER_FONT = str(app_s["WALLPAPER_FONT"])
            self.WALLPAPER_FONT_SIZE = int(app_s["WALLPAPER_FONT_SIZE"])
            self.WALLPAPER_FONT_FCOLOR = tuple(app_s["WALLPAPER_FONT_FCOLOR"])
            self.WALLPAPER_FONT_BCOLOR = tuple(app_s["WALLPAPER_FONT_BCOLOR"])

            # WEATHER settings
            weather_s = settings["WEATHER"]
            self.WEATHER_API_KEY = str(weather_s["WEATHER_API_KEY"])
            self.WEATHER_CITY = str(weather_s["WEATHER_CITY"])
            self.WEATHER_CUSTOM_ICO = bool(weather_s["WEATHER_CUSTOM_ICO"])
            self.WEATHER_ICON_FOLDER = str(weather_s["WEATHER_ICON_FOLDER"])
            self.WEATHER_ICON_SHADOW = bool(weather_s["WEATHER_ICON_SHADOW"])
            self.WEATHER_ICON_HIGHLIGHT = bool(weather_s["WEATHER_ICON_HIGHLIGHT"])
            self.WEATHER_ICON_SIZE = int(weather_s["WEATHER_ICON_SIZE"])
            self.WEATHER_LANG = str(weather_s["WEATHER_LANG"])

            # INFO settings
            info_s = settings["INFO"]
            self.INFO_USER = bool(info_s["INFO_USER"])
            self.INFO_HOST = bool(info_s["INFO_HOST"])
            self.INFO_TIME = bool(info_s["INFO_TIME"])
            self.INFO_DATE = bool(info_s["INFO_DATE"])
            self.INFO_LANS = bool(info_s["INFO_LANS"])
            self.INFO_CPU = bool(info_s["INFO_CPU"])
            self.INFO_RAM = bool(info_s["INFO_RAM"])

            # TABLE_SETTINGS
            table_s = settings["TABLE_SETTINGS"]
            self.BLUR_RADIUS = int(table_s["BLUR_RADIUS"]) # Blur for table background
            self.BACKGROUND_PADDING = int(table_s["BACKGROUND_PADDING"])
            self.CORNER_RADIUS = int(table_s["CORNER_RADIUS"])
            self.TABLE_PADDING = int(table_s["TABLE_PADDING"])
            self.TABLE_ROW_HEIGHT = int(table_s["TABLE_ROW_HEIGHT"])
            self.BACKGROUND_OPACITY = int(table_s["BACKGROUND_OPACITY"])
            self.TABLE_FONT_REGULAR = str(table_s["TABLE_FONT_REGULAR"])
            self.TABLE_FONT_BOLD = str(table_s["TABLE_FONT_BOLD"])
            self.TABLE_FONT_SIZE = int(table_s["TABLE_FONT_SIZE"])

        except KeyError as e:
            print(f"Error: Missing a required key in '{self.settings_file_path}': {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Error: Invalid value type in '{self.settings_file_path}'. Check key mentioned in: {e}")
            sys.exit(1)
            
        # Derived paths and constants
        self.SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ABS_WALLPAPER_FOLDER = os.path.join(self.SCRIPT_DIR, self.WALLPAPER_FOLDER)
        os.makedirs(self.ABS_WALLPAPER_FOLDER, exist_ok=True) # Ensure wallpaper folder exists
        
        # API URL constants
        self.BING_API_URL = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US"
        self.PEXELS_API_URL = "https://api.pexels.com/v1/search"
        self.OPENWEATHERMAP_URL_TEMPLATE = "http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}&lang={lang}"
        self.OPENWEATHERMAP_ICON_URL_TEMPLATE = "http://openweathermap.org/img/wn/{icon_code}@4x.png"
        self.NASA_APOD_URL_TEMPLATE = "https://api.nasa.gov/planetary/apod?api_key={api_key}&hd=True"
        self.PIXABAY_API_URL_TEMPLATE = "https://pixabay.com/api/?key={api_key}&per_page=50&safesearch=true&orientation=horizontal&q={category}"

    def print_summary(self):
        """Prints a short summary of critical loaded configurations."""
        print("--- Configuration Summary ---")
        print(f"  Wallpaper Folder: {self.ABS_WALLPAPER_FOLDER}")
        print(f"  Update Interval: {self.UPDATE_TIME} seconds")
        print(f"  Weather City: {self.WEATHER_CITY}")
        print(f"  Bing Download: {'Enabled' if self.DOWNLOAD_BING else 'Disabled'}")
        print(f"  NASA APOD Download: {'Enabled' if self.DOWNLOAD_NASA else 'Disabled'}")
        print(f"  Pixabay Download: {'Enabled' if self.DOWNLOAD_PIXABAY else 'Disabled'}")
        print(f"  Pexels Download: {'Enabled' if self.DOWNLOAD_PEXELS else 'Disabled'}")
        print("-----------------------------")

def process_and_save_image(config, image_url, output_filename, title=None, content=None, 
                           target_width=3840, target_height=2160, 
                           image_bg_blur_radius=30, # Renamed to distinguish from table blur
                           font_path=None, font_size=None, 
                           text_color=None, shadow_color=None, 
                           shadow_offset=3, margin=100):
    """
    Downloads an image, processes it (resize, blur background, add text), and saves it.
    Uses configuration for font details if not provided directly.
    """
    print("process_and_save_image")
    print(f"image_url: {image_url}")
    print(f"output_filename: {output_filename}")

    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        image_content = response.content
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None

    try:
        # Resize and create background
        image = Image.open(BytesIO(image_content)).convert("RGB")
        img_width, img_height = image.size
        ratio = min(target_width / img_width, target_height / img_height)
        resized_img_size = (int(img_width * ratio), int(img_height * ratio))
        img_resized = image.resize(resized_img_size, Image.LANCZOS)
        
        # Create a blurred background from the original image, scaled to target dimensions
        background = image.resize((target_width, target_height), Image.LANCZOS).filter(ImageFilter.GaussianBlur(image_bg_blur_radius))
        offset_x = (target_width - resized_img_size[0]) // 2
        offset_y = (target_height - resized_img_size[1]) // 2
        background.paste(img_resized, (offset_x, offset_y))
        image = background

        # Use config for font details if not provided
        font_path = font_path or config.WALLPAPER_FONT
        font_size = font_size or config.WALLPAPER_FONT_SIZE
        text_color = text_color or config.WALLPAPER_FONT_FCOLOR
        shadow_color = shadow_color or config.WALLPAPER_FONT_BCOLOR

        # Add text
        if title or content:
            draw = ImageDraw.Draw(image)
            try:
                font = ImageFont.truetype(font_path, font_size)
            except IOError:
                font = ImageFont.load_default()

            def draw_text_with_shadow(draw, position, text, font, text_color, shadow_color, shadow_offset):
                # Draw shadow
                draw.text((position[0] + shadow_offset, position[1] + shadow_offset), text, font=font, fill=shadow_color)
                draw.text((position[0] - shadow_offset, position[1] + shadow_offset), text, font=font, fill=shadow_color)
                draw.text((position[0] + shadow_offset, position[1] - shadow_offset), text, font=font, fill=shadow_color)
                draw.text((position[0] - shadow_offset, position[1] - shadow_offset), text, font=font, fill=shadow_color)
                # Draw main text
                draw.text(position, text, font=font, fill=text_color)

            if title:
                title_position = (margin, image.height - 200)
                draw_text_with_shadow(draw, title_position, title, font, text_color, shadow_color, shadow_offset)

            if content:
                content_position = (margin, image.height - 150)
                draw_text_with_shadow(draw, content_position, content, font, text_color, shadow_color, shadow_offset)

        # Save the processed image
        full_output_path = os.path.join(config.ABS_WALLPAPER_FOLDER, output_filename)
        image.save(full_output_path)
        print(f"Processed and saved: {output_filename}")
        return output_filename

    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def download_pixabay_image(config):
    """Downloads a random image from Pixabay based on configuration."""
    # Fetch JSON data from Pixabay API
    pixabay_api_url = config.PIXABAY_API_URL_TEMPLATE.format(
        api_key=config.DOWNLOAD_PIXABAY_API,
        category=config.DOWNLOAD_PIXABAY_CAT
    )
    try:
        response = requests.get(pixabay_api_url).json()    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from Pixabay API: {e}")
        return None
    if not response.get("hits"):
        print("No images found from Pixabay.")
        return None

    # Select a random image
    image_data = random.choice(response["hits"])
    image_url = image_data.get("largeImageURL")
    title = f"PIXABAY: {image_data.get("user")}"
    content = image_data.get("tags")
    
    file_name = f"{image_data.get('id')}.jpg"
    return process_and_save_image(config, image_url, file_name, title, content,
                                  font_path=config.WALLPAPER_FONT, font_size=config.WALLPAPER_FONT_SIZE,
                                  text_color=config.WALLPAPER_FONT_FCOLOR, shadow_color=config.WALLPAPER_FONT_BCOLOR)

def download_pexels_image(config):
    """Downloads a random image from Pexels based on configuration."""
    per_page = 50  # Number of images to fetch
    headers = {"Authorization": config.DOWNLOAD_PEXELS_API}
    params = {"query": config.DOWNLOAD_PEXELS_CAT, "per_page": per_page, "orientation": "landscape"}
    
    try:
        response = requests.get(config.PEXELS_API_URL, headers=headers, params=params).json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from Pexels API: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding Pexels API response.")
        return None


    if not response.get("photos"):
        print("No images found.")
        return None
    
    filtered_photos = [photo for photo in response["photos"] if "pixabay" not in photo["photographer"].lower()]
    if not filtered_photos:
        print("Only Pixabay images found, skipping.")
        return None
    
    # Select a random image
    image_data = random.choice(filtered_photos)
    image_url = image_data["src"]["original"]
    title = f"PEXELS: {image_data['photographer']}"
    content = image_data.get("alt", "No description available")
    
    file_name = f"{image_data['id']}.jpg"
    return process_and_save_image(config, image_url, file_name, title, content,
                                  font_path=config.WALLPAPER_FONT, font_size=config.WALLPAPER_FONT_SIZE,
                                  text_color=config.WALLPAPER_FONT_FCOLOR, shadow_color=config.WALLPAPER_FONT_BCOLOR)

def download_bing_wallpaper(config):
    """Downloads the Bing image of the day."""
    # Fetch JSON data from Bing API
    try:
        response = requests.get(config.BING_API_URL)
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to access Bing API: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding Bing API response.")
        return None

    # Extract image details
    image = data["images"][0]
    image_url = "https://www.bing.com" + image["urlbase"] + "_UHD.jpg"
    image_date = image["fullstartdate"]  # Example: "20240317"    
    title = f"BING: {image["title"]}"    # e.g., "A Beautiful Landscape"
    content = image["copyright"]  # e.g., "Image by XYZ"

    # Create the file name
    file_name = f"{image_date}.jpg"
    return process_and_save_image(config, image_url, file_name, title, content,
                                  font_path=config.WALLPAPER_FONT, font_size=config.WALLPAPER_FONT_SIZE,
                                  text_color=config.WALLPAPER_FONT_FCOLOR, shadow_color=config.WALLPAPER_FONT_BCOLOR)

def download_nasa_apod(config):
    """Downloads NASA's Astronomy Picture of the Day (APOD)."""
    # Fetch JSON data from NASA API
    nasa_api_url = config.NASA_APOD_URL_TEMPLATE.format(api_key=config.DOWNLOAD_NASA_API)
    try:
        response_obj = requests.get(nasa_api_url)
        response_obj.raise_for_status()
        response = response_obj.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to access NASA APOD API: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding NASA APOD API response.")
        return None
    # Extract image details
    image_url = response.get("hdurl")
    image_date = response.get("date")  # Example: "20240317"
    content = response.get("explanation")  # e.g., "Image by XYZ"
    title = f"NASA: {response.get("title")}"  # e.g., "A Beautiful Landscape"
    media_type = response.get("media_type")
    
    if media_type == "video":
        print("NASA APOD is a video. Requesting fallback.")
        return "NASA_VIDEO_FALLBACK_REQUESTED"

    # Create the file name
    file_name = f"{image_date}.jpg"
    return process_and_save_image(config, image_url, file_name, title, content,
                                  font_path=config.WALLPAPER_FONT, font_size=config.WALLPAPER_FONT_SIZE,
                                  text_color=config.WALLPAPER_FONT_FCOLOR, shadow_color=config.WALLPAPER_FONT_BCOLOR)

def get_wallpaper_path():
    """Retrieves the current desktop wallpaper path from the Windows Registry."""
    # This function is Windows-specific.
    try:        
        reg_key = r"Control Panel\Desktop"    
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key)        
        wallpaper_path, _ = winreg.QueryValueEx(key, "WallPaper")
        winreg.CloseKey(key)
        return wallpaper_path
    except Exception as e:
        print(f"Error getting current wallpaper path from registry: {e}")
        return None

def get_weather(config, table_data):
    """Fetches weather information and appends it to table_data."""
    try:
        url = config.OPENWEATHERMAP_URL_TEMPLATE.format(
            city=config.WEATHER_CITY,
            api_key=config.WEATHER_API_KEY,
            lang=config.WEATHER_LANG
        )
        response_obj = requests.get(url)
        response_obj.raise_for_status() # Raise an exception for HTTP errors
        data = response_obj.json()
        # If raise_for_status() didn't raise an error, the request was successful (2xx)
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
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        table_data.append(("Weather :", "Connection error"))
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error parsing weather data: {e}")
        table_data.append(("Weather :", "Data parsing error"))
        return None    
        
def get_weather_icon(config, icon_code):
    """
    Retrieves the weather icon image. 
    Uses a custom icon if configured and available, otherwise downloads from OpenWeatherMap.
    """
    try:
        print(f"icon code={icon_code}")
        icons_folder = os.path.join(config.SCRIPT_DIR, config.WEATHER_ICON_FOLDER)
        os.makedirs(icons_folder, exist_ok=True)  # Ensure the folder exists
        local_icon_path = os.path.join(icons_folder, f"{icon_code}.png")
        
        if config.WEATHER_CUSTOM_ICO:
            if os.path.exists(local_icon_path):
                print(f"Using custom weather icon: {local_icon_path}")
                return Image.open(local_icon_path)
            else:
                print(f"Warning: Custom weather icon enabled but '{local_icon_path}' not found. No icon will be displayed.")
                return None # Explicitly return None if custom icon is missing
        
        # If not using custom icons, or if custom icon was not found (and we decided to fallback - current logic does not fallback here)
        icon_url = config.OPENWEATHERMAP_ICON_URL_TEMPLATE.format(icon_code=icon_code)
        print(f"Downloading weather icon from: {icon_url}")
        response_obj = requests.get(icon_url)
        response_obj.raise_for_status()
        icon_image = Image.open(BytesIO(response_obj.content))            
        return icon_image

    except Exception as e:
        print(f"Error fetching weather icon: {e}")    
        return None

def get_pc_info(config, table_data):
    """Fetches PC information (User, Host) and appends it to table_data."""
    try:
        if config.INFO_USER:
            username = getpass.getuser()
            table_data.append(("User :", username))
        
        if config.INFO_HOST:
            hostname = socket.gethostname()
            table_data.append(("Host :", hostname))
    except Exception as e:
        print(f"Error get_pc_info: {e}")

def get_cpu_infos(config, table_data):
    """Fetches CPU information and appends it to table_data."""
    try:
        if config.INFO_CPU:
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

def get_ram_infos(config, table_data):
    """Fetches RAM information and appends it to table_data."""
    try:
        if config.INFO_RAM:
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

def get_network_infos(config, table_data):
    """Fetches network interface information and appends it to table_data."""
    try:
        if config.INFO_LANS:
            table_data.append(("", ""))
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

def get_date_time(config, table_data):
    """Fetches current date and time and appends to table_data based on config."""
    try:
        if config.INFO_TIME:
            last_update_time = f"{datetime.datetime.now().strftime('%H:%M:%S')}"        
            table_data.append(("", ""))
            table_data.append(("Update Time :", last_update_time))
            
        if config.INFO_DATE:
            today_date = f"{datetime.datetime.now().strftime('%Y-%m-%d')}"
            table_data.append(("", ""))
            table_data.append(("Date :", today_date))
    except Exception as e:
        print(f"Error get_date_time: {e}")

def backup_wallpaper(config, wallpaper_path):
    """
    Creates a backup of the given wallpaper in a 'backup' subfolder 
    within the main wallpaper directory. Overwrites if backup already exists.
    Returns the path to the backup file, or None on error.
    """
    try:
        # Backups will be stored in a subfolder of our main wallpaper folder
        backup_base_folder = os.path.join(config.ABS_WALLPAPER_FOLDER, "backup")
        os.makedirs(backup_base_folder, exist_ok=True)  # Ensure the backup folder exists

        image_filename = os.path.basename(wallpaper_path)
        # Create the backup file path
        backup_file_path = os.path.join(backup_base_folder, image_filename)

        # Check if a backup file exists
        if os.path.exists(backup_file_path): # Always re-create/overwrite the backup
            # To ensure we are working on a fresh copy of wallpaper_path for modification
            print(f"Re-creating backup for: {wallpaper_path} at {backup_file_path}")
            Image.open(wallpaper_path).save(backup_file_path) # Overwrite or create
        else:
            print("No backup file found. Creating a new backup.")
            # Copy the selected image to the backup folder
            image = Image.open(wallpaper_path)  # Open the original image
            image.save(backup_file_path)  # Save it as a backup
            
        return backup_file_path
    except Exception as e:
        print(f"Error backup_wallpaper: {e}")
        return None

def add_weather_icon(config, image, weather_icon_code, width, table_width, table_y_offset):
    """Adds the weather icon to the wallpaper image if available."""
    try:
        if weather_icon_code:
            print (f"icon code{weather_icon_code}")
            icon_image = get_weather_icon(config, weather_icon_code)
            if not icon_image: # If icon couldn't be loaded/downloaded
                return
            
            # Resize the icon        
            new_width = config.WEATHER_ICON_SIZE
            aspect_ratio = new_width / icon_image.width
            new_height = int(icon_image.height * aspect_ratio)
            icon_size = (new_width, new_height)        
            icon_image = icon_image.resize(icon_size, Image.Resampling.LANCZOS)
            icon_image = icon_image.convert("RGBA")
            
            icon_x = width - (table_width + new_width) // 2 
            icon_y = table_y_offset - 80 
            
            # Add a highlight effect for the icon
            if config.WEATHER_ICON_HIGHLIGHT:
                highlight_layer = Image.new("RGBA", icon_size, (255, 255, 255, 0))
                highlight_draw = ImageDraw.Draw(highlight_layer)
                highlight_draw.ellipse(
                    [10, 10, icon_size[0] - 10, icon_size[1] - 10],
                    fill=(255, 255, 255, 100)
                )
                image.alpha_composite(highlight_layer, (icon_x, icon_y)) # Use alpha_composite for RGBA images

            # Add shadow for the icon
            if config.WEATHER_ICON_SHADOW:
                shadow_icon = icon_image.copy().convert("RGBA")
                shadow_icon = shadow_icon.filter(ImageFilter.GaussianBlur(10))
                shadow_position = (icon_x + 5, icon_y + 5)
                image.alpha_composite(shadow_icon, shadow_position) # Use alpha_composite

            # Paste the icon on its original position
            image.paste(icon_image, (icon_x, icon_y), icon_image)
    except Exception as e:
        print(f"Error add_weather_icon: {e}")

def set_wallpaper(file_path):    
    """Sets the desktop wallpaper for Windows."""
    # Constants for SystemParametersInfoW
    SPI_SETDESKWALLPAPER = 20
    SPIF_UPDATEINIFILE = 0x01  # Writes the new system-wide parameter setting to the user profile.
    SPIF_SENDWININICHANGE = 0x02 # Broadcasts the WM_SETTINGCHANGE message to all top-level windows.

    # Ensure the file path is absolute. This is good practice,
    # though in the current script flow, file_path should already be absolute.
    abs_file_path = os.path.abspath(file_path)

    # Call SystemParametersInfoW to set the wallpaper.
    # SPIF_UPDATEINIFILE ensures the change is saved.
    # The desktop wallpaper itself should still update.
    result = ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, abs_file_path, SPIF_UPDATEINIFILE)

    if result:
        print(f"Successfully set wallpaper to: {abs_file_path}")
    else:
        # SystemParametersInfoW returns a non-zero value if successful.
        print(f"Failed to set wallpaper using SystemParametersInfoW. Return code: {result}")
        # For further debugging, one might check ctypes.get_last_error()


def update_wallpaper(config):
    """Main function to update the desktop wallpaper with system information."""
    try:
        image_name = None # Will store the filename of the downloaded image

        if config.DOWNLOAD_NASA:
            nasa_result = download_nasa_apod(config)
            if nasa_result == "NASA_VIDEO_FALLBACK_REQUESTED":
                if config.DOWNLOAD_BING:
                    print("NASA APOD was video, attempting Bing fallback.")
                    image_name = download_bing_wallpaper(config)
                else:
                    print("NASA APOD was video, but Bing downloads are disabled. No new image.")
            else: # nasa_result is filename or None
                image_name = nasa_result
        elif config.DOWNLOAD_BING:
            image_name = download_bing_wallpaper(config)
        elif config.DOWNLOAD_PIXABAY:
            image_name = download_pixabay_image(config)
        elif config.DOWNLOAD_PEXELS:
            image_name = download_pexels_image(config)

        source_image_for_this_run = None
        if image_name: # A new image was successfully downloaded
            source_image_for_this_run = os.path.join(config.ABS_WALLPAPER_FOLDER, image_name)
            print(f"Using newly downloaded image: {source_image_for_this_run}")
        else:
            print("No new image downloaded or selected. Using current system wallpaper.")
            current_system_wallpaper = get_wallpaper_path()
            if not current_system_wallpaper:
                print(f"Error: Failed to get current system wallpaper path or path invalid: '{current_system_wallpaper}'. Skipping update.")
                return
            source_image_for_this_run = current_system_wallpaper
            print(f"Using current system wallpaper: {source_image_for_this_run}")

        # Create/use a working copy (backup) of the source image for modification
        path_to_load_and_modify = backup_wallpaper(config, source_image_for_this_run)
        if not path_to_load_and_modify:
            print(f"Error creating/accessing working copy for {source_image_for_this_run}. Skipping update.")
            return
        
        print(f"Processing image: {path_to_load_and_modify}")
        # Load and process the image
        image = Image.open(path_to_load_and_modify)
        image = image.convert("RGB")  # Convert from RGBA to RGB if needed

        # Set the font for the text
        try:
            font = ImageFont.truetype(config.TABLE_FONT_REGULAR, config.TABLE_FONT_SIZE)
            bold_font = ImageFont.truetype(config.TABLE_FONT_BOLD, config.TABLE_FONT_SIZE)
        except IOError:
            print(f"Warning: Could not load custom table fonts ({config.TABLE_FONT_REGULAR}, {config.TABLE_FONT_BOLD}). Using default font.")
            font = ImageFont.load_default()
            bold_font = font
        
        table_data = [("", "")]
        
        get_pc_info(config, table_data)
        get_cpu_infos(config, table_data)
        get_network_infos(config, table_data)
        get_ram_infos(config, table_data)
        get_date_time(config, table_data)
        weather_icon_code = get_weather(config, table_data)
        
        # Calculate table dimensions
        draw = ImageDraw.Draw(image)
        # Calculate the maximum width of text in the table
        max_text_width = 0
        if table_data: # Ensure table_data is not empty
             # Use default=0 for max() to handle cases where the generator is empty
             # (e.g., if table_data only contains entries that are filtered out by 'if name or value')
             max_text_width = max((draw.textbbox((0, 0), f"{name}: {value}", font=font)[2]
                                   for name, value in table_data if name or value),
                                  default=0)
        table_width = max_text_width + 2 * config.TABLE_PADDING
        # Calculate the total height of the table
        table_height = len(table_data) * config.TABLE_ROW_HEIGHT + 2 * config.TABLE_PADDING

        # Draw a rounded rectangle for the table background
        width, height = image.size
        table_background_rect = (
            width - table_width - 10,
            10,
            width - 10,
            table_height + 10 + (50 if weather_icon_code else 0)  # Add extra space for the icon
        )

        # Black background color with transparency
        background_color = (0, 0, 0, config.BACKGROUND_OPACITY)

        # Draw the background with transparency
        shadow_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.rounded_rectangle(table_background_rect, fill=background_color, radius=config.CORNER_RADIUS)
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(config.BLUR_RADIUS))
        image = Image.alpha_composite(image.convert("RGBA"), shadow_layer)

        # Add table text to the top-right corner
        table_y_offset = table_background_rect[1] + config.TABLE_PADDING
        for data_name, data_value in table_data:
            table_text_left = str(data_name)  # Convert iface_name to string
            table_text_right = str(data_value)  # Convert iface_ip to string

            draw = ImageDraw.Draw(image)
            draw.text((table_background_rect[0] + config.TABLE_PADDING, table_y_offset), table_text_left, font=font, fill="white")

            # Calculate text dimensions for right-aligned text
            text_bbox = draw.textbbox((0, 0), table_text_right, font=bold_font)
            text_width = text_bbox[2] - text_bbox[0]

            # Position for right-aligned text
            draw.text((width - config.TABLE_PADDING - text_width - 10, table_y_offset), table_text_right, font=bold_font, fill="yellow")  # Bold yellow text, -10 for right margin
            table_y_offset += config.TABLE_ROW_HEIGHT

        # Add weather icon to the bottom of the table
        add_weather_icon(config, image, weather_icon_code, width, table_width, table_y_offset)    

        # Save the updated image as the new wallpaper
        image.convert("RGB").save(path_to_load_and_modify) # Save changes back to the working copy
        print(f"Processed wallpaper saved to: '{path_to_load_and_modify}'.")

        # Set the new wallpaper as the desktop background
        set_wallpaper(path_to_load_and_modify)
        print("New wallpaper set as the desktop background.")
    except Exception as e:
        print(f"Error update_wallpaper: {e}")
        
def main():
    """Main function to run the wallpaper update process in a loop."""
    config = AppConfig()
    config.print_summary()

    while True:
        try:
            update_wallpaper(config)
            sleep_duration = config.UPDATE_TIME
            print(f"Waiting for {sleep_duration} seconds before next update...")
            time.sleep(sleep_duration)
        except KeyboardInterrupt:
            print("\nApplication terminated by user.")
            break
        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")
            print("Waiting for 60 seconds before retrying...")
            time.sleep(60) # Wait a bit before retrying on generic error

if __name__ == "__main__":
    main()
