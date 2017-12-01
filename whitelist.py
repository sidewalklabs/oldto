# whitelist of methods for vulture dead code detection
from whitelist_utils import Whitelist

# Vulture doesn't understand Flask routing.
whitelist_server = Whitelist()
whitelist_server.by_location
whitelist_server.by_photo_id
whitelist_server.lat_lng_counts
