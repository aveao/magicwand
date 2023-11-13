import requests
import time
import logging
from requests.auth import HTTPBasicAuth


class TailscaleAPI:
    API_BASE = "https://api.tailscale.com/api/v2"
    api_key = None
    api_key_expiry = None

    def __init__(self, tailnet_id: str = "-"):
        self.tailnet_id = tailnet_id

    def auth_with_api_key(self, api_key: str):
        self.api_key = api_key

    def auth_with_oauth_client(self, client_id: str, client_secret: str) -> dict:
        oauth2_basic_auth = HTTPBasicAuth(
            client_id,
            client_secret,
        )
        req = requests.post(
            "https://api.tailscale.com/api/v2/oauth/token",
            auth=oauth2_basic_auth,
        )
        req.raise_for_status()
        reqj = req.json()

        self.api_key = reqj["access_token"]
        self.api_key_expiry = time.monotonic() + reqj["expires_in"]
        logging.debug("OAuth2 payload: %s", reqj)

        # Save client ID and secret now that we know they're good
        self.client_id = client_id
        self.client_secret = client_secret

    def get_devices(self) -> dict:
        if not self.api_key:
            raise Exception("Tailscale API key not supplied!")
        # if API key is about to expire / has already expired, renew it
        # unlikely in magicwand but eh
        elif self.api_key_expiry and (time.monotonic() + 5 >= self.api_key_expiry):
            self.auth_with_oauth_client(self.client_id, self.client_secret)

        url = f"{self.API_BASE}/tailnet/{self.tailnet_id}/devices"

        req = requests.get(url, headers={"Authorization": f"Bearer {self.api_key}"})
        req.raise_for_status()
        reqj = req.json()
        return reqj["devices"]
