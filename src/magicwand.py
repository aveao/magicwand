#!/usr/bin/python3
from collections import defaultdict
import logging
import argparse
from cf_api import create_cf_dns_record_object, CloudflareAPI
from ts_api import TailscaleAPI


def split_a_aaaa(ip_list: list) -> dict:
    output_dict = {}
    for ip in ip_list:
        record_type = "A" if "." in ip else "AAAA"
        output_dict[record_type] = ip
    return output_dict


def generate_ts_dns_records(ts_api_inst: TailscaleAPI) -> dict:
    ts_devices = ts_api_inst.get_devices()
    dns_mappings = {}
    for ts_device in ts_devices:
        # Convert "laserjet.raccoon-cardassian.ts.net" to "laserjet"
        # (hostname field allows spaces etc)
        device_subdomain = ts_device["name"].split(".")[0]
        dns_mappings[device_subdomain] = split_a_aaaa(ts_device["addresses"])
    return dns_mappings


def filter_cf_dns(cf_dns_records: dict, suffix: str) -> dict:
    dns_mappings = defaultdict(dict)
    for dns_record in cf_dns_records:
        # Convert "whatever.ts.example.com" to "whatever.ts"
        subdomain_name = (
            dns_record["name"].replace(dns_record["zone_name"], "").strip(".")
        )
        # Only return DNS records that are used by magicwand
        # Only return A or AAAA records
        if not subdomain_name.endswith(suffix) or dns_record["type"] not in [
            "A",
            "AAAA",
        ]:
            continue

        dns_mappings[subdomain_name][dns_record["type"]] = {
            "ip": dns_record["content"],
            "id": dns_record["id"],
        }
    return dict(dns_mappings)


def sync_ts_dns_to_cloudflare_dns(
    cf_api_inst: dict,
    cf_zone_id: str,
    cf_suffix: str,
    cf_dns_records: dict,
    ts_dns_records: dict,
):
    for base_subdomain, ts_ip_addresses in ts_dns_records.items():
        subdomain = base_subdomain + cf_suffix
        for record_type, ip_address in ts_ip_addresses.items():
            if (
                subdomain not in cf_dns_records
                or record_type not in cf_dns_records[subdomain]
            ):
                logging.info(f"Creating {subdomain}:{ip_address}")
                dns_record_object = create_cf_dns_record_object(subdomain, ip_address)
                cf_api_inst.create_dns_record(cf_zone_id, dns_record_object)
            elif cf_dns_records[subdomain][record_type]["ip"] != ip_address:
                logging.info(f"Updating {subdomain}:{ip_address}")
                dns_record_object = create_cf_dns_record_object(subdomain, ip_address)
                dns_record_identifier = cf_dns_records[subdomain][record_type]["id"]
                cf_api_inst.put_dns_record(
                    cf_zone_id,
                    dns_record_identifier,
                    dns_record_object,
                )
            else:
                logging.debug(f"No need to change {subdomain}:{ip_address}")


def clean_cloudflare_dns(
    cf_api_inst: dict,
    cf_zone_id: str,
    cf_suffix: str,
    cf_dns_records: dict,
    ts_dns_records: dict,
):
    for subdomain, cf_record_data in cf_dns_records.items():
        # Convert "whatever.ts" to "whatever"
        clean_subdomain = subdomain[: -len(cf_suffix)]
        if clean_subdomain not in ts_dns_records:
            logging.info(f"Deleting {subdomain}")
            for record_type in cf_dns_records[subdomain]:
                dns_record_identifier = cf_dns_records[subdomain][record_type]["id"]
                cf_api_inst.delete_dns_record(
                    cf_zone_id,
                    dns_record_identifier,
                )


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='"Simple" script to sync Tailscale MagicDNS to Cloudflare DNS.'
    )

    parser.add_argument(
        "--ts_client_id", required=True, help="Tailscale OAuth2 Client ID"
    )
    parser.add_argument(
        "--ts_client_secret", required=True, help="Tailscale OAuth2 Client Secret"
    )
    parser.add_argument("--cf_apikey", required=True, help="Cloudflare API Key")
    parser.add_argument("--cf_zone_id", required=True, help="Cloudflare Zone ID")
    parser.add_argument(
        "--cf_suffix",
        default=".ts",
        help='Cloudflare Subdomain Suffix (default: ".ts")',
    )
    parser.add_argument(
        "--log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_arguments()
    logging.basicConfig(level=args.log_level)

    ts_api_inst = TailscaleAPI()
    ts_api_inst.auth_with_oauth_client(args.ts_client_id, args.ts_client_secret)
    logging.info("Authenticated to tailscale via OAuth2.")
    ts_dns_records = generate_ts_dns_records(ts_api_inst)
    logging.info("Fetched Tailscale MagicDNS data (%i devices).", len(ts_dns_records))
    logging.debug("Generated Tailscale DNS records: %s", ts_dns_records)

    cf_api_inst = CloudflareAPI(args.cf_apikey)
    cf_dns_records_raw = cf_api_inst.get_dns_records(args.cf_zone_id)
    logging.debug("Fetched Cloudflare DNS records: %s", cf_dns_records_raw)

    cf_dns_records = filter_cf_dns(cf_dns_records_raw, args.cf_suffix)
    logging.info(
        "Fetched Cloudflare DNS data (%i magicwand records, %i total).",
        len(cf_dns_records),
        len(cf_dns_records_raw),
    )
    logging.debug("Generated Cloudflare DNS records: %s", cf_dns_records)

    sync_ts_dns_to_cloudflare_dns(
        cf_api_inst, args.cf_zone_id, args.cf_suffix, cf_dns_records, ts_dns_records
    )

    clean_cloudflare_dns(
        cf_api_inst, args.cf_zone_id, args.cf_suffix, cf_dns_records, ts_dns_records
    )

    logging.info(f"All done! {len(ts_dns_records)} records synced.")
