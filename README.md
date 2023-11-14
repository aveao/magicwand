# magicwand

"Simple" script to sync Tailscale MagicDNS to Cloudflare DNS. Fun little evening project.

## Have you ever been in this situation?

- You want to use MagicDNS?
- You don't want your local DNS server replaced with 100.100.100.100?
- You go on your favorite search engine to find if there's a way to make your MagicDNS DNS entries available when not using the MagicDNS resolver, and see that it's not possible? 

Then magicwand is for you!

## Usage

You'll need a relatively modern python version, at least post-3.6. 

- Install requirements in `src` dir by running `pip3 install -r requirements.txt` in it (but tbh it only really installs requests and you likely have it installed anyways).
- Obtain your Tailscale OAuth Client ID and Secret from https://login.tailscale.com/admin/settings/oauth (scope of `devices:read` is sufficient)
- Obtain your Cloudflare API key from https://dash.cloudflare.com/profile/api-tokens (scope of `DNS.Edit` for the domain you want to use is sufficient)
- Obtain your Cloudflare Zone ID from the domain's Overview page, in the bottom right (as of late 2023) in the API section.

Put it together like so:

`python3 magicwand.py --ts_client_id "aaaaaaaaaaaa" --ts_client_secret "tskey-client-aaaaaaaaaaaa-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" --cf_apikey "aaaaaaaaa-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" --cf_zone_id "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"`

and then do as you please, crontab it or smth:

`0 * * * * cd /home/ave/magicwand/src && python3 magicwand.py --ts_client_id "aaaaaaaaaaaa" --ts_client_secret "tskey-client-aaaaaaaaaaaa-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" --cf_apikey "aaaaaaaaa-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" --cf_zone_id "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"`

(helpful: https://crontab.guru/)

### Additional flags

- By default it uses `.ts` as the suffix (so `hostname` becomes `hostname.ts.example.com`), you can change this with `--cf_suffix`. You can theoretically set anything, including empty string.
- If for some reason you don't want it to clean up the DNS entries no longer in use (removed devices, changed suffix etc), you can do so with `--disable_cleanup`.
- If you want to remove all magicwand DNS entries from a server, you can do so with `--undo_magicwand`.

## Limitations

Tailscale is annoying and does not expose shared-in devices when you're using OAuth. API key works around this but those can only be generated with a lifetime of up to 90 days, which is also annoying.
