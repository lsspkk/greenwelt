Map Data Files Documentation
=============================

mapX_config.json
----------------
name                 - Display name for the map
total_orders         - Total number of orders in the map
orders_required      - Orders player must complete to finish map
plants_required      - Plants player must deliver to finish map (alternative win condition)
batch_size           - Number of orders selected for each incoming batch
batch_delay          - Seconds between batches when no orders are incoming/visible
accept_time          - Seconds player has to accept a visible order before it expires
active_order_limit   - Maximum accepted orders before new batches stop appearing
greenery             - Greenery overlay settings (enabled, green_color, white_threshold)

mapX_orders.json
----------------
Format: { "LocationName": [ orders... ] }

Each order:
  order_id       - Unique identifier for the order
  send_time      - Max random delay (seconds) before order becomes visible (rolls between send_time/2 and send_time)
  plants         - List of plant requests

Each plant:
  plant_filename  - Image filename
  plant_name_fi   - Finnish name
  plant_name_en   - English name
  amount          - Quantity requested

mapX_locations.json
-------------------
List of map locations with position and type info.

mapX_roads.json
---------------
Road path data for collision detection.
