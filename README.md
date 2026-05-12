# magicwand

"Simple" script to sync Tailscale MagicDNS to Cloudflare DNS. Fun little evening project.

## Have you ever been in this situation?

- You want to use MagicDNS?
- You don't want your local DNS server replaced with 100.100.100.100?
- You go on your favorite search engine to find if there's a way to make your MagicDNS DNS entries available when not using the MagicDNS resolver, and see that it's not possible?

Then magicwand is for you!

## Usage

You'll want to use `uv`, see [here](https://docs.astral.sh/uv/getting-started/installation/) for installation instructions.

- Obtain your Tailscale OAuth Client ID and Secret from https://login.tailscale.com/admin/settings/oauth (scope of `devices:core:read` is sufficient)
- Obtain your Cloudflare API key from https://dash.cloudflare.com/?to=/:account/api-tokens (scope of `DNS Read` and `DNS Edit` for the domain you want to use is sufficient)
- Obtain your Cloudflare Zone ID from the domain's Overview page, in the bottom right (as of mid 2026) in the API section.

Put it together like so:

`uv run magicwand --ts_client_id "aaaaaaaaaaaa" --ts_client_secret "tskey-client-aaaaaaaaaaaa-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" --cf_apikey "aaaaaaaaa-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" --cf_zone_id "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"`

and then do as you please, crontab it or smth:

`0 * * * * cd /home/ave/magicwand/src && uv run magicwand --ts_client_id "aaaaaaaaaaaa" --ts_client_secret "tskey-client-aaaaaaaaaaaa-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" --cf_apikey "aaaaaaaaa-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" --cf_zone_id "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"`

(helpful: https://crontab.guru/)

### Additional flags

- By default it uses `.ts` as the suffix (so `hostname` becomes `hostname.ts.example.com`), you can change this with `--cf_suffix`. You can theoretically set anything, including empty string.
- If for some reason you don't want it to clean up the DNS entries no longer in use (removed devices, changed suffix etc), you can do so with `--disable_cleanup`.
- If you want to remove all magicwand DNS entries from a server, you can do so with `--undo_magicwand`.

## Limitations

Tailscale is annoying and does not expose shared-in devices when you're using OAuth. API key works around this but those can only be generated with a lifetime of up to 90 days, which is also annoying.

## SSH Config Hint

You might want to add a line like this to your SSH config:

```
CanonicalizeHostname yes
CanonicalDomains home local ts.example.com
CanonicalizeMaxDots 0
```

When you run `ssh my-computer`, this will first try to resolve `my-computer.home`, then `my-computer.local`, then `my-computer.ts.example.com`, and if that fails it'll try to resolve `my-computer` with your local resolver and it's search domain(s). This gives a mostly MagicDNS-like experience for SSH.

As a note on the shortcomings of this approach:
- search domains provided by your local resolver will only be tried as a last resort, and trying to connect to a tailscale IP can sometimes hang if you're not connected.
- the match rules will be applied as a double-pass by default. This can e.g. override the Host-specific users you might've set. Use `final` where appropriate, e.g. `Match all`/`Match *` -> `Match final all`.
