"""
Map Order Tool - Creates plant order data for game maps.
See map_order_specification.txt for details.

Uses tkinter for UI (standard Python library).
Run with: python tools/map_order.py

Requires: pip install pillow
"""

import json
import logging
import os
import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk

from PIL import Image, ImageTk

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"
PLANTS_DIR = ASSETS_DIR / "plants" / "one"
CONFIG_FILE = SCRIPT_DIR / "map_order.yaml"
PSEUDO_EMAIL_FILE = DATA_DIR / "pseudo-email.json"

logger.info(f"Project root: {PROJECT_ROOT}")
logger.info(f"Assets dir: {ASSETS_DIR}")
logger.info(f"Data dir: {DATA_DIR}")
logger.info(f"Plants dir: {PLANTS_DIR}")

# UI sizing constants
FONT_SMALL = ('TkDefaultFont', 12)
FONT_MEDIUM = ('TkDefaultFont', 14)
FONT_LARGE = ('TkDefaultFont', 16, 'bold')
FONT_XLARGE = ('TkDefaultFont', 18, 'bold')
PLANT_IMAGE_SIZE = 80  # Size of plant thumbnails in pixels
BUTTON_PADDING = 8


def load_yaml_simple(filepath):
    """
    Simple YAML loader for our specific format.
    Only handles our plants list structure.
    """
    logger.debug(f"Loading YAML from {filepath}")
    plants = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_plant = None
    
    for line in lines:
        line = line.rstrip()
        
        # Skip comments and empty lines
        if not line or line.strip().startswith('#'):
            continue
        
        # Check for new plant entry
        if '- filename:' in line:
            if current_plant is not None:
                plants.append(current_plant)
            # Extract filename value
            value = line.split(':', 1)[1].strip().strip('"')
            current_plant = {'filename': value}
        elif current_plant is not None:
            if 'fi:' in line:
                value = line.split(':', 1)[1].strip().strip('"')
                current_plant['fi'] = value
            elif 'en:' in line:
                value = line.split(':', 1)[1].strip().strip('"')
                current_plant['en'] = value
    
    # Don't forget last plant
    if current_plant is not None:
        plants.append(current_plant)
    
    logger.debug(f"Loaded {len(plants)} plants from YAML")
    return {'plants': plants}


def load_pseudo_emails():
    """Load pseudo email data from JSON."""
    logger.debug(f"Loading pseudo emails from {PSEUDO_EMAIL_FILE}")
    
    if not PSEUDO_EMAIL_FILE.exists():
        logger.warning("Pseudo email file not found, using defaults")
        return {
            'usernames': ['user1', 'user2', 'user3'],
            'domains': ['example.com', 'test.fi']
        }
    
    with open(PSEUDO_EMAIL_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.debug(f"Loaded {len(data.get('usernames', []))} usernames and {len(data.get('domains', []))} domains")
    return data


def generate_unique_email(existing_emails, email_data):
    """Generate a unique email that doesn't exist in existing_emails."""
    logger.debug(f"Generating unique email, {len(existing_emails)} existing emails")
    
    usernames = email_data.get('usernames', [])
    domains = email_data.get('domains', [])
    
    if not usernames or not domains:
        logger.error("No usernames or domains available")
        return "unknown@example.com"
    
    # Try up to 100 times to find unique combination
    for attempt in range(100):
        username = random.choice(usernames)
        domain = random.choice(domains)
        email = f"{username}@{domain}"
        
        if email not in existing_emails:
            logger.debug(f"Generated unique email: {email} (attempt {attempt + 1})")
            return email
    
    # Fallback: add number suffix
    base_username = random.choice(usernames)
    domain = random.choice(domains)
    suffix = random.randint(100, 999)
    email = f"{base_username}{suffix}@{domain}"
    logger.debug(f"Generated fallback email with suffix: {email}")
    return email


def get_all_emails_in_map(locations):
    """Get all existing emails from locations."""
    emails = set()
    for loc in locations:
        email = loc.get('email')
        if email:
            emails.add(email)
    return emails


class PlantData:
    """Holds plant configuration data."""
    
    def __init__(self):
        self.plants = []
        self.images = {}  # filename -> PhotoImage
        self.load()
    
    def load(self):
        """Load plants from YAML config."""
        logger.info("Loading plant data")
        
        if not CONFIG_FILE.exists():
            logger.error(f"Config file not found: {CONFIG_FILE}")
            return
        
        data = load_yaml_simple(CONFIG_FILE)
        self.plants = data.get('plants', [])
        logger.info(f"Loaded {len(self.plants)} plants")
    
    def load_images(self):
        """Load and resize plant images for display."""
        logger.info("Loading plant images")
        
        for plant in self.plants:
            filename = plant.get('filename', '')
            image_path = PLANTS_DIR / filename
            
            if image_path.exists():
                try:
                    # Load and resize image
                    img = Image.open(image_path)
                    img = img.resize((PLANT_IMAGE_SIZE, PLANT_IMAGE_SIZE), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.images[filename] = photo
                    logger.debug(f"Loaded image: {filename}")
                except Exception as e:
                    logger.warning(f"Failed to load image {filename}: {e}")
            else:
                logger.warning(f"Image not found: {image_path}")
        
        logger.info(f"Loaded {len(self.images)} plant images")
    
    def get_image(self, filename):
        """Get PhotoImage for a plant filename."""
        return self.images.get(filename)
    
    def get_plant_by_filename(self, filename):
        """Find plant by filename."""
        for plant in self.plants:
            if plant.get('filename') == filename:
                return plant
        return None


class MapData:
    """Holds map data (locations and orders)."""
    
    def __init__(self, map_name):
        self.map_name = map_name
        self.locations = []
        self.orders = {}  # location_name -> list of orders
        self.map_image_path = None
        self.locations_modified = False
    
    def load(self):
        """Load map data from files."""
        logger.info(f"Loading map data for {self.map_name}")
        
        # Load locations
        locations_file = DATA_DIR / f"{self.map_name}_locations.json"
        if locations_file.exists():
            with open(locations_file, 'r', encoding='utf-8') as f:
                self.locations = json.load(f)
            logger.info(f"Loaded {len(self.locations)} locations")
        else:
            logger.warning(f"Locations file not found: {locations_file}")
        
        # Load orders
        orders_file = DATA_DIR / f"{self.map_name}_orders.json"
        if orders_file.exists():
            with open(orders_file, 'r', encoding='utf-8') as f:
                self.orders = json.load(f)
            logger.info(f"Loaded orders for {len(self.orders)} locations")
        else:
            logger.info("No existing orders file")
            self.orders = {}
        
        # Find map image
        for ext in ['.png', '.jpg']:
            img_path = ASSETS_DIR / f"{self.map_name}{ext}"
            if img_path.exists():
                self.map_image_path = img_path
                logger.info(f"Found map image: {img_path}")
                break
    
    def save(self):
        """Save orders to file."""
        logger.info(f"Saving map data for {self.map_name}")

        # Generate order_ids for all orders
        order_id_prefix = self.map_name + "-order-"
        order_counter = 1
        for location_name, orders_list in self.orders.items():
            for order in orders_list:
                order['order_id'] = f"{order_id_prefix}{order_counter}"
                order_counter += 1

        # Save orders
        orders_file = DATA_DIR / f"{self.map_name}_orders.json"
        with open(orders_file, 'w', encoding='utf-8') as f:
            json.dump(self.orders, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved orders to {orders_file}")
        
        # Save locations if modified (for email updates)
        if self.locations_modified:
            locations_file = DATA_DIR / f"{self.map_name}_locations.json"
            with open(locations_file, 'w', encoding='utf-8') as f:
                json.dump(self.locations, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved locations to {locations_file}")
            self.locations_modified = False
    
    def get_location_by_name(self, name):
        """Find location by name."""
        for loc in self.locations:
            if loc.get('name') == name:
                return loc
        return None
    
    def get_orders_for_location(self, location_name):
        """Get orders list for a location."""
        if location_name not in self.orders:
            self.orders[location_name] = []
        return self.orders[location_name]
    
    def set_location_email(self, location_name, email):
        """Set email for a location."""
        loc = self.get_location_by_name(location_name)
        if loc:
            loc['email'] = email
            self.locations_modified = True
            logger.debug(f"Set email for {location_name}: {email}")


class OrderDialog(tk.Toplevel):
    """Dialog to edit a single order's plant list."""
    
    def __init__(self, parent, order, plant_data, on_save):
        super().__init__(parent)
        self.order = order
        self.plant_data = plant_data
        self.on_save = on_save
        
        self.title("Tilaus")
        self.geometry("1200x800")
        self.transient(parent)
        
        # Wait for window to be visible before grabbing
        self.wait_visibility()
        self.grab_set()
        
        logger.debug(f"Opening order dialog with {len(order.get('plants', []))} plants")
        
        self.create_widgets()
        self.load_order_data()
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Main container
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for send_time
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(top_frame, text="Lähetysaika (1-9):", font=FONT_MEDIUM).pack(side=tk.LEFT)
        self.send_time_var = tk.StringVar(value="5")
        self.send_time_spin = ttk.Spinbox(top_frame, from_=1, to=9, width=5, 
                                           textvariable=self.send_time_var, font=FONT_MEDIUM)
        self.send_time_spin.pack(side=tk.LEFT, padx=8)
        
        self.random_time_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top_frame, text="Random", variable=self.random_time_var,
                        command=self.on_random_time_toggle).pack(side=tk.LEFT, padx=15)
        
        ttk.Label(top_frame, text="Min:", font=FONT_MEDIUM).pack(side=tk.LEFT)
        self.time_min_var = tk.StringVar(value="1")
        self.time_min_spin = ttk.Spinbox(top_frame, from_=1, to=9, width=5,
                                          textvariable=self.time_min_var, state='disabled', font=FONT_MEDIUM)
        self.time_min_spin.pack(side=tk.LEFT, padx=4)
        
        ttk.Label(top_frame, text="Max:", font=FONT_MEDIUM).pack(side=tk.LEFT)
        self.time_max_var = tk.StringVar(value="9")
        self.time_max_spin = ttk.Spinbox(top_frame, from_=1, to=9, width=5,
                                          textvariable=self.time_max_var, state='disabled', font=FONT_MEDIUM)
        self.time_max_spin.pack(side=tk.LEFT, padx=4)
        
        # Content frame with two sides
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - plant picker with images
        left_frame = ttk.LabelFrame(content_frame, text="Kasvit (klikkaa lisätäksesi)", padding=8)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Plant grid with scrollbar
        self.plant_canvas = tk.Canvas(left_frame, width=500, height=500)
        plant_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, 
                                         command=self.plant_canvas.yview)
        self.plant_frame = ttk.Frame(self.plant_canvas)
        
        self.plant_canvas.configure(yscrollcommand=plant_scrollbar.set)
        plant_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.plant_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.plant_canvas_window = self.plant_canvas.create_window(
            (0, 0), window=self.plant_frame, anchor=tk.NW)
        
        self.plant_frame.bind("<Configure>", self.on_plant_frame_configure)
        self.plant_canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Bind mousewheel scrolling
        self.plant_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.plant_canvas.bind("<Button-4>", self.on_mousewheel)
        self.plant_canvas.bind("<Button-5>", self.on_mousewheel)
        
        self.create_plant_grid()
        
        # Right side - order plants as cards
        right_frame = ttk.LabelFrame(content_frame, text="Tilauksen kasvit", padding=8)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Scrollable area for plant cards
        self.order_canvas = tk.Canvas(right_frame, width=450, height=450)
        order_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, 
                                         command=self.order_canvas.yview)
        self.order_cards_frame = ttk.Frame(self.order_canvas)
        
        self.order_canvas.configure(yscrollcommand=order_scrollbar.set)
        order_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.order_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.order_canvas_window = self.order_canvas.create_window(
            (0, 0), window=self.order_cards_frame, anchor=tk.NW)
        
        self.order_cards_frame.bind("<Configure>", self.on_order_frame_configure)
        self.order_canvas.bind("<Configure>", self.on_order_canvas_configure)
        
        # Bind mousewheel scrolling for order canvas
        self.order_canvas.bind("<MouseWheel>", self.on_order_mousewheel)
        self.order_canvas.bind("<Button-4>", self.on_order_mousewheel)
        self.order_canvas.bind("<Button-5>", self.on_order_mousewheel)
        
        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(bottom_frame, text="OK", command=self.save_and_close).pack(
            side=tk.RIGHT, padx=4, ipadx=20, ipady=BUTTON_PADDING)
        ttk.Button(bottom_frame, text="Keskeytä", command=self.destroy).pack(
            side=tk.RIGHT, padx=4, ipadx=10, ipady=BUTTON_PADDING)

    def on_plant_frame_configure(self, event):
        """Update scrollregion when plant frame changes."""
        self.plant_canvas.configure(scrollregion=self.plant_canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        """Update frame width when canvas changes."""
        self.plant_canvas.itemconfig(self.plant_canvas_window, width=event.width)
    
    def on_order_frame_configure(self, event):
        """Update scrollregion when order frame changes."""
        self.order_canvas.configure(scrollregion=self.order_canvas.bbox("all"))
    
    def on_order_canvas_configure(self, event):
        """Update frame width when order canvas changes."""
        self.order_canvas.itemconfig(self.order_canvas_window, width=event.width)
    
    def on_mousewheel(self, event):
        """Handle mousewheel scrolling on plant canvas."""
        # Linux uses Button-4 (up) and Button-5 (down)
        if event.num == 4:
            self.plant_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.plant_canvas.yview_scroll(1, "units")
        else:
            # Windows/Mac
            self.plant_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_order_mousewheel(self, event):
        """Handle mousewheel scrolling on order canvas."""
        if event.num == 4:
            self.order_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.order_canvas.yview_scroll(1, "units")
        else:
            self.order_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_random_time_toggle(self):
        """Toggle random time inputs."""
        if self.random_time_var.get():
            self.time_min_spin.configure(state='normal')
            self.time_max_spin.configure(state='normal')
            self.send_time_spin.configure(state='disabled')
        else:
            self.time_min_spin.configure(state='disabled')
            self.time_max_spin.configure(state='disabled')
            self.send_time_spin.configure(state='normal')
    
    def create_plant_grid(self):
        """Create grid of plant image buttons."""
        logger.debug("Creating plant grid with images")
        
        self.plant_buttons = []
        
        row = 0
        col = 0
        columns = 4  # 4 columns for image grid
        
        for plant in self.plant_data.plants:
            filename = plant.get('filename', '')
            fi_name = plant.get('fi', filename)
            
            # Create frame for each plant (image + label)
            plant_item_frame = ttk.Frame(self.plant_frame)
            plant_item_frame.grid(row=row, column=col, padx=6, pady=6)
            
            # Get plant image
            image = self.plant_data.get_image(filename)
            
            if image:
                # Create button with image
                btn = tk.Button(
                    plant_item_frame,
                    image=image,
                    command=lambda p=plant: self.add_plant(p),
                    relief=tk.RAISED,
                    borderwidth=2,
                    cursor="hand2"
                )
            else:
                # Fallback to text button if image not available
                btn = tk.Button(
                    plant_item_frame,
                    text="?",
                    width=8,
                    height=4,
                    command=lambda p=plant: self.add_plant(p),
                    cursor="hand2"
                )
            
            btn.pack()
            
            # Add plant name label below image
            name_label = ttk.Label(plant_item_frame, text=fi_name, font=FONT_SMALL)
            name_label.pack()
            
            self.plant_buttons.append(btn)
            
            col += 1
            if col >= columns:
                col = 0
                row += 1
        
        logger.debug(f"Created {len(self.plant_buttons)} plant image buttons")
    
    def load_order_data(self):
        """Load existing order data into UI."""
        # Load send time
        send_time = self.order.get('send_time', {})
        if isinstance(send_time, dict):
            self.random_time_var.set(True)
            self.time_min_var.set(str(send_time.get('min', 1)))
            self.time_max_var.set(str(send_time.get('max', 9)))
            self.on_random_time_toggle()
        else:
            self.send_time_var.set(str(send_time) if send_time else "5")
        
        # Load plants
        self.update_order_cards()
    
    def update_order_cards(self):
        """Update the order plants as card rows with buttons."""
        # Clear existing cards
        for widget in self.order_cards_frame.winfo_children():
            widget.destroy()
        
        plants = self.order.get('plants', [])
        
        if not plants:
            empty_label = ttk.Label(self.order_cards_frame, text="Ei kasveja", font=FONT_MEDIUM)
            empty_label.pack(pady=20)
            return
        
        for index, plant in enumerate(plants):
            self.create_plant_card(index, plant)
    
    def create_plant_card(self, index, plant):
        """Create a card row for a plant in the order."""
        fi_name = plant.get('plant_name_fi', plant.get('plant_filename', '?'))
        current_amount = plant.get('amount', 1)
        filename = plant.get('plant_filename', '')
        
        # Card frame with border
        card_frame = ttk.Frame(self.order_cards_frame, relief=tk.RIDGE, borderwidth=2)
        card_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Top row: plant image (small) + name + remove button
        top_row = ttk.Frame(card_frame)
        top_row.pack(fill=tk.X, padx=8, pady=8)
        
        # Small plant image
        image = self.plant_data.get_image(filename)
        if image:
            img_label = ttk.Label(top_row, image=image)
            img_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Plant name
        name_label = ttk.Label(top_row, text=fi_name, font=FONT_MEDIUM)
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Remove button
        remove_btn = tk.Button(
            top_row, 
            text="Poista", 
            command=lambda idx=index: self.remove_plant(idx),
            bg="#ffcccc",
            cursor="hand2",
            font=FONT_SMALL
        )
        remove_btn.pack(side=tk.RIGHT, padx=5)
        
        # Bottom row: amount label + number buttons 1-9
        bottom_row = ttk.Frame(card_frame)
        bottom_row.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        amount_label = ttk.Label(bottom_row, text="Määrä:", font=FONT_SMALL)
        amount_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Number buttons 1-9
        for num in range(1, 10):
            # Highlight current amount
            if num == current_amount:
                btn = tk.Button(
                    bottom_row,
                    text=str(num),
                    width=3,
                    command=lambda idx=index, n=num: self.set_amount(idx, n),
                    bg="#4CAF50",
                    fg="white",
                    font=FONT_SMALL,
                    cursor="hand2"
                )
            else:
                btn = tk.Button(
                    bottom_row,
                    text=str(num),
                    width=3,
                    command=lambda idx=index, n=num: self.set_amount(idx, n),
                    font=FONT_SMALL,
                    cursor="hand2"
                )
            btn.pack(side=tk.LEFT, padx=2)
    
    def add_plant(self, plant):
        """Add plant to order."""
        logger.debug(f"Adding plant: {plant.get('fi')}")

        if 'plants' not in self.order:
            self.order['plants'] = []

        plant_entry = {
            'plant_filename': plant.get('filename'),
            'plant_name_fi': plant.get('fi'),
            'plant_name_en': plant.get('en'),
            'amount': 1
        }
        self.order['plants'].append(plant_entry)
        self.update_order_cards()

    def remove_plant(self, index):
        """Remove plant from order by index."""
        plants = self.order.get('plants', [])
        if 0 <= index < len(plants):
            removed = plants.pop(index)
            logger.debug(f"Removed plant: {removed.get('plant_name_fi')}")
            self.update_order_cards()

    def set_amount(self, index, amount):
        """Set amount for plant at index."""
        plants = self.order.get('plants', [])
        if 0 <= index < len(plants):
            plants[index]['amount'] = amount
            logger.debug(f"Set amount to {amount} for plant at index {index}")
            self.update_order_cards()

    def save_and_close(self):
        """Save order data and close."""

        # Save send time
        if self.random_time_var.get():
            try:
                min_val = int(self.time_min_var.get())
                max_val = int(self.time_max_var.get())
                self.order['send_time'] = {'min': min_val, 'max': max_val}
            except ValueError:
                self.order['send_time'] = {'min': 1, 'max': 9}
        else:
            try:
                self.order['send_time'] = int(self.send_time_var.get())
            except ValueError:
                self.order['send_time'] = 5

        logger.debug(f"Saving order with {len(self.order.get('plants', []))} plants")
        self.on_save(self.order)
        self.destroy()


class LocationDialog(tk.Toplevel):
    """Dialog to manage orders for a location."""
    
    def __init__(self, parent, location, map_data, plant_data, email_data, on_save):
        super().__init__(parent)
        self.location = location
        self.map_data = map_data
        self.plant_data = plant_data
        self.email_data = email_data
        self.on_save = on_save
        
        location_name = location.get('name', 'Unknown')
        self.title(f"Tilaukset - {location_name}")
        self.geometry("700x550")
        self.transient(parent)
        
        # Wait for window to be visible before grabbing
        self.wait_visibility()
        self.grab_set()
        
        self.orders = map_data.get_orders_for_location(location_name).copy()
        
        logger.debug(f"Opening location dialog for {location_name}, {len(self.orders)} orders")
        
        self.create_widgets()
        self.update_order_list()
    
    def create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Location info
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        loc_name = self.location.get('name', 'Unknown')
        loc_type = self.location.get('type', 'unknown')
        loc_email = self.location.get('email', 'Ei sähköpostia')
        
        ttk.Label(info_frame, text=f"{loc_name} ({loc_type})", 
                  font=FONT_XLARGE).pack(anchor=tk.W)
        
        self.email_label = ttk.Label(info_frame, text=f"Email: {loc_email}", font=FONT_MEDIUM)
        self.email_label.pack(anchor=tk.W)
        
        # Orders list
        list_frame = ttk.LabelFrame(main_frame, text="Tilaukset", padding=8)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable frame for orders
        order_canvas = tk.Canvas(list_frame, height=300)
        order_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=order_canvas.yview)
        self.order_frame = ttk.Frame(order_canvas)
        
        order_canvas.configure(yscrollcommand=order_scrollbar.set)
        order_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        order_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.order_canvas_window = order_canvas.create_window((0, 0), window=self.order_frame, anchor=tk.NW)
        
        # Configure scroll region
        self.order_frame.bind("<Configure>", 
            lambda e: order_canvas.configure(scrollregion=order_canvas.bbox("all")))
        order_canvas.bind("<Configure>", 
            lambda e: order_canvas.itemconfig(self.order_canvas_window, width=e.width))

        # Button frame at bottom of orders list
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Lisää tilaus", command=self.add_order).pack(
            side=tk.LEFT, padx=4, ipadx=BUTTON_PADDING, ipady=BUTTON_PADDING)
        
        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(bottom_frame, text="OK", command=self.save_and_close).pack(
            side=tk.RIGHT, padx=4, ipadx=20, ipady=BUTTON_PADDING)
        ttk.Button(bottom_frame, text="Keskeytä", command=self.destroy).pack(
            side=tk.RIGHT, padx=4, ipadx=10, ipady=BUTTON_PADDING)
    
    def update_order_list(self):
        """Update the orders list in the order_frame."""
        # Clear the current order_frame
        for widget in self.order_frame.winfo_children():
            widget.destroy()

        if not self.orders:
            empty_label = ttk.Label(self.order_frame, text="Ei tilauksia", font=FONT_MEDIUM)
            empty_label.pack(pady=20)
            return

        # Recreate rows for each order
        for i, order in enumerate(self.orders):
            self.create_order_card(i, order)

    def create_order_card(self, index, order):
        """Create a card for an order."""
        plants = order.get('plants', [])
        send_time = order.get('send_time', 5)
        
        # Format send time display
        if isinstance(send_time, dict):
            time_str = f"Aika: {send_time.get('min', 1)}-{send_time.get('max', 9)}"
        else:
            time_str = f"Aika: {send_time}"
        
        # Format plants summary
        if plants:
            plant_names = []
            for p in plants:
                name = p.get('plant_name_fi', '?')
                amount = p.get('amount', 1)
                plant_names.append(f"{name} x{amount}")
            plants_str = ", ".join(plant_names)
        else:
            plants_str = "Ei kasveja"
        
        # Card frame
        card_frame = ttk.Frame(self.order_frame, relief=tk.RIDGE, borderwidth=2)
        card_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Top row: order number + time
        top_row = ttk.Frame(card_frame)
        top_row.pack(fill=tk.X, padx=8, pady=(8, 4))
        
        order_label = ttk.Label(top_row, text=f"Tilaus {index + 1}", font=FONT_MEDIUM)
        order_label.pack(side=tk.LEFT)
        
        time_label = ttk.Label(top_row, text=time_str, font=FONT_SMALL)
        time_label.pack(side=tk.LEFT, padx=20)
        
        # Middle row: plants
        plants_label = ttk.Label(card_frame, text=plants_str, font=FONT_SMALL, wraplength=500)
        plants_label.pack(fill=tk.X, padx=8, pady=4)
        
        # Bottom row: buttons
        btn_row = ttk.Frame(card_frame)
        btn_row.pack(fill=tk.X, padx=8, pady=(4, 8))
        
        ttk.Button(btn_row, text="Muokkaa", 
            command=lambda idx=index: self.edit_order(idx)).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Poista", 
            command=lambda idx=index: self.remove_order(idx)).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Ylös", 
            command=lambda idx=index: self.move_up(idx)).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Alas", 
            command=lambda idx=index: self.move_down(idx)).pack(side=tk.LEFT, padx=4)

    def add_order(self):
        """Add a new order."""
        new_order = {
            'send_time': 5,
            'plants': []
        }
        self.orders.append(new_order)
        
        # Open edit dialog for the new order
        index = len(self.orders) - 1
        OrderDialog(self, new_order, self.plant_data, 
            lambda updated_order: self.save_order(index, updated_order))

    def edit_order(self, index):
        """Edit selected order."""
        if 0 <= index < len(self.orders):
            order = self.orders[index]
            OrderDialog(self, order, self.plant_data, 
                lambda updated_order: self.save_order(index, updated_order))

    def remove_order(self, index):
        """Remove selected order."""
        if 0 <= index < len(self.orders):
            self.orders.pop(index)
            self.update_order_list()

    def move_up(self, index):
        """Move order up in the list."""
        if index > 0 and index < len(self.orders):
            self.orders[index], self.orders[index - 1] = self.orders[index - 1], self.orders[index]
            self.update_order_list()

    def move_down(self, index):
        """Move order down in the list."""
        if index >= 0 and index < len(self.orders) - 1:
            self.orders[index], self.orders[index + 1] = self.orders[index + 1], self.orders[index]
            self.update_order_list()

    def save_order(self, index, updated_order):
        """Save the updated order back to the list."""
        if 0 <= index < len(self.orders):
            self.orders[index] = updated_order
            self.update_order_list()

    def save_and_close(self):
        """Save orders and close dialog."""
        location_name = self.location.get('name')
        
        # Update map data with orders
        self.map_data.orders[location_name] = self.orders
        
        # Assign email if missing
        if not self.location.get('email'):
            existing_emails = get_all_emails_in_map(self.map_data.locations)
            new_email = generate_unique_email(existing_emails, self.email_data)
            self.map_data.set_location_email(location_name, new_email)
            logger.info(f"Assigned email {new_email} to {location_name}")
        
        logger.debug(f"Saving {len(self.orders)} orders for {location_name}")
        self.on_save()
        self.destroy()


class MapOrderApp:
    """Main application window."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Tilaustyökalu")
        self.root.geometry("1400x900")
        
        self.plant_data = PlantData()
        self.plant_data.load_images()  # Load plant images after tkinter is initialized
        self.email_data = load_pseudo_emails()
        self.map_data = None
        self.available_maps = []
        
        logger.info("Starting Map Order App")
        
        self.find_available_maps()
        self.create_widgets()
    
    def find_available_maps(self):
        """Find available maps in data folder."""
        logger.debug("Finding available maps")
        
        self.available_maps = []
        
        if not DATA_DIR.exists():
            logger.warning(f"Data directory not found: {DATA_DIR}")
            return
        
        for f in DATA_DIR.iterdir():
            if f.name.endswith('_locations.json'):
                map_name = f.name.replace('_locations.json', '')
                self.available_maps.append(map_name)
                logger.debug(f"Found map: {map_name}")
        
        logger.info(f"Found {len(self.available_maps)} maps")
    
    def create_widgets(self):
        """Create main window widgets."""
        # Top toolbar
        toolbar = ttk.Frame(self.root, padding=10)
        toolbar.pack(fill=tk.X)
        
        ttk.Label(toolbar, text="Kartta:", font=FONT_MEDIUM).pack(side=tk.LEFT)
        
        self.map_var = tk.StringVar()
        self.map_combo = ttk.Combobox(toolbar, textvariable=self.map_var, 
                                       values=self.available_maps, state='readonly', width=20, font=FONT_MEDIUM)
        self.map_combo.pack(side=tk.LEFT, padx=8)
        self.map_combo.bind('<<ComboboxSelected>>', self.on_map_selected)
        
        ttk.Button(toolbar, text="Lataa", command=self.load_map).pack(side=tk.LEFT, padx=8, ipadx=BUTTON_PADDING, ipady=BUTTON_PADDING)
        ttk.Button(toolbar, text="Tallenna", command=self.save_map).pack(side=tk.LEFT, padx=8, ipadx=BUTTON_PADDING, ipady=BUTTON_PADDING)
        
        # Roll all emails button
        ttk.Button(toolbar, text="Arvo kaikki emailit", command=self.roll_all_emails).pack(side=tk.LEFT, padx=8, ipadx=BUTTON_PADDING, ipady=BUTTON_PADDING)
        
        # Status label
        self.status_var = tk.StringVar(value="Valitse kartta")
        ttk.Label(toolbar, textvariable=self.status_var, font=FONT_MEDIUM).pack(side=tk.RIGHT, padx=15)
        
        # Main content area
        content_frame = ttk.Frame(self.root, padding=15)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - map info and location cards
        left_frame = ttk.Frame(content_frame, width=600)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        left_frame.pack_propagate(False)
        
        # Map info
        self.map_info_label = ttk.Label(left_frame, text="Ei karttaa ladattu", 
                                         font=FONT_XLARGE)
        self.map_info_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Locations as cards (scrollable)
        loc_frame = ttk.LabelFrame(left_frame, text="Sijainnit", padding=8)
        loc_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable canvas for location cards
        self.location_canvas = tk.Canvas(loc_frame)
        loc_scrollbar = ttk.Scrollbar(loc_frame, orient=tk.VERTICAL, 
                                       command=self.location_canvas.yview)
        self.location_cards_frame = ttk.Frame(self.location_canvas)
        
        self.location_canvas.configure(yscrollcommand=loc_scrollbar.set)
        loc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.location_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.location_canvas_window = self.location_canvas.create_window(
            (0, 0), window=self.location_cards_frame, anchor=tk.NW)
        
        # Configure scroll region
        self.location_cards_frame.bind("<Configure>", 
            lambda e: self.location_canvas.configure(scrollregion=self.location_canvas.bbox("all")))
        self.location_canvas.bind("<Configure>", 
            lambda e: self.location_canvas.itemconfig(self.location_canvas_window, width=e.width))
        
        # Bind mousewheel scrolling
        self.location_canvas.bind("<MouseWheel>", self.on_location_mousewheel)
        self.location_canvas.bind("<Button-4>", self.on_location_mousewheel)
        self.location_canvas.bind("<Button-5>", self.on_location_mousewheel)
        
        # Right side - summary
        right_frame = ttk.LabelFrame(content_frame, text="Yhteenveto", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.summary_text = tk.Text(right_frame, wrap=tk.WORD, state=tk.DISABLED, font=FONT_SMALL)
        summary_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, 
                                           command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scrollbar.set)
        summary_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # Select first map if available
        if self.available_maps:
            self.map_combo.current(0)
    
    def on_location_mousewheel(self, event):
        """Handle mousewheel scrolling on location canvas."""
        if event.num == 4:
            self.location_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.location_canvas.yview_scroll(1, "units")
        else:
            self.location_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_map_selected(self, event=None):
        """Handle map selection change."""
        logger.debug(f"Map selected: {self.map_var.get()}")
    
    def load_map(self):
        """Load selected map."""
        map_name = self.map_var.get()
        if not map_name:
            messagebox.showwarning("Varoitus", "Valitse kartta ensin")
            return
        
        logger.info(f"Loading map: {map_name}")
        
        self.map_data = MapData(map_name)
        self.map_data.load()
        
        self.map_info_label.configure(text=f"Kartta: {map_name}")
        self.status_var.set(f"Ladattu: {map_name}")
        
        self.update_location_list()
        self.update_summary()
    
    def save_map(self):
        """Save current map data."""
        if not self.map_data:
            messagebox.showwarning("Varoitus", "Ei karttaa ladattu")
            return
        
        self.map_data.save()
        self.status_var.set(f"Tallennettu: {self.map_data.map_name}")
        messagebox.showinfo("Tallennettu", "Tiedot tallennettu!")
    
    def update_location_list(self):
        """Update locations as card rows."""
        # Clear existing cards
        for widget in self.location_cards_frame.winfo_children():
            widget.destroy()
        
        if not self.map_data:
            empty_label = ttk.Label(self.location_cards_frame, text="Lataa kartta ensin", font=FONT_MEDIUM)
            empty_label.pack(pady=20)
            return
        
        if not self.map_data.locations:
            empty_label = ttk.Label(self.location_cards_frame, text="Ei sijainteja", font=FONT_MEDIUM)
            empty_label.pack(pady=20)
            return
        
        for index, loc in enumerate(self.map_data.locations):
            self.create_location_card(index, loc)
    
    def create_location_card(self, index, location):
        """Create a card row for a location."""
        name = location.get('name', '?')
        loc_type = location.get('type', '?')
        email = location.get('email', '')
        
        orders = self.map_data.get_orders_for_location(name)
        order_count = len(orders)
        
        # Card frame with border
        card_frame = ttk.Frame(self.location_cards_frame, relief=tk.RIDGE, borderwidth=2)
        card_frame.pack(fill=tk.X, padx=5, pady=3)
        
        # Top row: location name + type + order count
        top_row = ttk.Frame(card_frame)
        top_row.pack(fill=tk.X, padx=8, pady=(8, 4))
        
        name_label = ttk.Label(top_row, text=f"{name}", font=FONT_MEDIUM)
        name_label.pack(side=tk.LEFT)
        
        type_label = ttk.Label(top_row, text=f"({loc_type})", font=FONT_SMALL)
        type_label.pack(side=tk.LEFT, padx=10)
        
        orders_label = ttk.Label(top_row, text=f"{order_count} tilausta", font=FONT_SMALL)
        orders_label.pack(side=tk.LEFT, padx=10)
        
        # Middle row: email
        email_row = ttk.Frame(card_frame)
        email_row.pack(fill=tk.X, padx=8, pady=2)
        
        if email:
            email_text = email
            email_color = "#006600"
        else:
            email_text = "Ei sähköpostia"
            email_color = "#990000"
        
        email_label = ttk.Label(email_row, text=f"Email: {email_text}", font=FONT_SMALL)
        email_label.pack(side=tk.LEFT)
        
        # Bottom row: buttons
        btn_row = ttk.Frame(card_frame)
        btn_row.pack(fill=tk.X, padx=8, pady=(4, 8))
        
        ttk.Button(btn_row, text="Muokkaa tilauksia", 
            command=lambda idx=index: self.edit_location_orders_by_index(idx)).pack(side=tk.LEFT, padx=4)
        
        tk.Button(btn_row, text="Arvo email", 
            command=lambda idx=index: self.roll_email_for_location(idx),
            bg="#e6f3ff",
            cursor="hand2",
            font=FONT_SMALL).pack(side=tk.LEFT, padx=4)
    
    def roll_email_for_location(self, index):
        """Roll a new unique email for a specific location."""
        if not self.map_data:
            return
        
        if 0 <= index < len(self.map_data.locations):
            location = self.map_data.locations[index]
            location_name = location.get('name')
            
            existing_emails = get_all_emails_in_map(self.map_data.locations)
            
            # Remove current email from existing set so we can regenerate
            current_email = location.get('email')
            if current_email and current_email in existing_emails:
                existing_emails.remove(current_email)
            
            new_email = generate_unique_email(existing_emails, self.email_data)
            self.map_data.set_location_email(location_name, new_email)
            
            logger.info(f"Rolled new email for {location_name}: {new_email}")
            
            self.update_location_list()
            self.update_summary()
    
    def roll_all_emails(self):
        """Roll unique emails for all locations."""
        if not self.map_data:
            messagebox.showwarning("Varoitus", "Lataa kartta ensin")
            return
        
        count = 0
        for location in self.map_data.locations:
            location_name = location.get('name')
            existing_emails = get_all_emails_in_map(self.map_data.locations)
            
            new_email = generate_unique_email(existing_emails, self.email_data)
            self.map_data.set_location_email(location_name, new_email)
            count += 1
        
        logger.info(f"Rolled emails for {count} locations")
        self.status_var.set(f"Arvottu {count} sähköpostia")
        
        self.update_location_list()
        self.update_summary()
    
    def edit_location_orders_by_index(self, index):
        """Open dialog to edit orders for location at given index."""
        if not self.map_data:
            return
        
        if 0 <= index < len(self.map_data.locations):
            location = self.map_data.locations[index]
            
            def on_save():
                self.update_location_list()
                self.update_summary()
            
            LocationDialog(
                self.root, 
                location, 
                self.map_data, 
                self.plant_data, 
                self.email_data,
                on_save
            )
    
    def update_summary(self):
        """Update summary text."""
        self.summary_text.configure(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        if not self.map_data:
            self.summary_text.insert(tk.END, "Ei karttaa ladattu")
            self.summary_text.configure(state=tk.DISABLED)
            return
        
        lines = []
        lines.append(f"Kartta: {self.map_data.map_name}\n")
        lines.append(f"Sijainteja: {len(self.map_data.locations)}\n")
        
        total_orders = 0
        locations_with_orders = 0
        locations_with_email = 0
        
        for loc in self.map_data.locations:
            name = loc.get('name')
            orders = self.map_data.get_orders_for_location(name)
            
            if orders:
                locations_with_orders += 1
                total_orders += len(orders)
            
            if loc.get('email'):
                locations_with_email += 1
        
        lines.append(f"Sijainteja tilauksilla: {locations_with_orders}\n")
        lines.append(f"Sijainteja sähköpostilla: {locations_with_email}\n")
        lines.append(f"Tilauksia yhteensä: {total_orders}\n")
        lines.append("\n--- Tilaukset sijainneittain ---\n\n")
        
        for loc in self.map_data.locations:
            name = loc.get('name')
            email = loc.get('email', 'Ei sähköpostia')
            orders = self.map_data.get_orders_for_location(name)
            
            if orders:
                lines.append(f"{name} ({email}):\n")
                for i, order in enumerate(orders):
                    plants = order.get('plants', [])
                    plant_names = [p.get('plant_name_fi', '?') for p in plants]
                    lines.append(f"  Tilaus {i+1}: {', '.join(plant_names)}\n")
                lines.append("\n")
        
        self.summary_text.insert(tk.END, ''.join(lines))
        self.summary_text.configure(state=tk.DISABLED)
    
    def edit_location_orders(self, event=None):
        """Open dialog to edit orders for first location (legacy, use edit_location_orders_by_index instead)."""
        if not self.map_data:
            return
        
        if self.map_data.locations:
            self.edit_location_orders_by_index(0)


def main():
    """Main entry point."""
    logger.info("Starting Map Order Tool")
    
    root = tk.Tk()
    app = MapOrderApp(root)
    
    logger.info("Entering main loop")
    root.mainloop()
    
    logger.info("Application closed")


if __name__ == '__main__':
    main()
