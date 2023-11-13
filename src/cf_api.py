import requests
import logging


def create_cf_dns_record_object(
    name: str,
    ip: str,
    comment: str = "Created by magicwand",
):
    # hacky?
    record_type = "A" if "." in ip else "AAAA"

    record_data = {
        "content": ip,
        "name": name,
        "proxied": False,
        "type": record_type,
        "comment": comment,
    }
    return record_data


class CloudflareAPI:
    API_BASE = "https://api.cloudflare.com/client/v4"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _do_request(self, url: str, request_type: str, additional_arguments: dict = {}):
        logging.debug(
            "Requesting %s with type %s and arguments %s",
            url,
            request_type,
            additional_arguments,
        )

        req = requests.request(
            request_type,
            url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            **additional_arguments,
        )
        req.raise_for_status()
        return req

    def _get_with_pagination(self, url: str) -> list:
        result = []
        page_count = 1
        while True:
            req = self._do_request(
                url, "GET", {"params": {"per_page": 100, "page": page_count}}
            )
            reqj = req.json()
            logging.debug("Got page %i for URL %s", page_count, url)
            result += reqj["result"]
            if reqj["result_info"]["total_pages"] == page_count:
                break
            page_count += 1
        return result

    def get_dns_records(self, zone_identifier: str) -> dict:
        url = f"{self.API_BASE}/zones/{zone_identifier}/dns_records"

        return self._get_with_pagination(url)

    def delete_dns_record(self, zone_identifier: str, dns_record_identifier: str):
        url = (
            f"{self.API_BASE}/zones/{zone_identifier}"
            f"/dns_records/{dns_record_identifier}"
        )

        self._do_request(url, "DELETE")

    def create_dns_record(
        self,
        zone_identifier: str,
        record_data: dict,
    ):
        url = f"{self.API_BASE}/zones/{zone_identifier}/dns_records"

        self._do_request(url, "POST", {"json": record_data})

    def put_dns_record(
        self,
        zone_identifier: str,
        dns_record_identifier: str,
        record_data: dict,
    ):
        url = (
            f"{self.API_BASE}/zones/{zone_identifier}"
            f"/dns_records/{self.dns_record_identifier}"
        )

        self._do_request(url, "PUT", {"json": record_data})
