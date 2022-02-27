"""Constants used by the iDiamant component."""
from homeassistant.const import Platform

NAME = "iDiamant"
VERSION = "0.0.1"
DOMAIN = "idiamant"
DOMAIN_DATA = f"{DOMAIN}_data"

MANUFACTURER = "Netatmo"
DEFAULT_ATTRIBUTION = f"Data provided by {MANUFACTURER}"

PLATFORMS = [
    Platform.COVER,
    Platform.SENSOR,
]

BASE_API_URL = "https://api.netatmo.com"
API_PATH = "/api"

TIMEOUT = 10

ACCEPT_HEADER = "Accept"
ACCEPT_HEADER_JSON = "application/json"
AUTHORIZATION_HEADER = "Authorization"
AUTHORIZATION_HEADER_BEARER = "Bearer"
DEFAULT_HEADERS = {ACCEPT_HEADER: ACCEPT_HEADER_JSON}

OAUTH2_PATH = "/oauth2"
OAUTH2_AUTHORIZE_URL = BASE_API_URL + OAUTH2_PATH + "/authorize"
OAUTH2_TOKEN_URL = BASE_API_URL + OAUTH2_PATH + "/token"

SCOPES = [
    "read_bubendorff",
    "write_bubendorff",
]

MODEL_NBG = "Gateway"
MODEL_NBR = "Rolling shutter"
MODEL_NBO = "Orientable shutter"
MODEL_NBS = "Swinging shutter"

MODELS = {
    "NBG": MODEL_NBG,
    "NBR": MODEL_NBR,
    "NBO": MODEL_NBO,
    "NBS": MODEL_NBS,
}

TYPE_SECURITY = "security"

AUTH = "idiamant_auth"

DATA_HOMES = ("idiamant_homes",)
DATA_ROOMS = ("idiamant_rooms",)
DATA_MODULES = ("idiamant_modules",)
