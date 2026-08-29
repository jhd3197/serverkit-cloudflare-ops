# ServerKit Cloudflare Zone Ops

[<img src="https://serverkit.ai/badge/install.png" alt="Install in ServerKit" width="240">](https://serverkit.ai/i/ext/serverkit-cloudflare-ops)

Per-zone Cloudflare operations for [ServerKit](https://github.com/jhd3197/ServerKit),
packaged as a first-party extension. Layered on the panel's Cloudflare DNS
connection, reached from the "Open in Cloudflare" button on a
Cloudflare-managed domain:

- **Zone settings** — SSL/TLS mode, HSTS, Speed and Caching toggles with a
  one-click hardening preset, plus cache purge.
- **WAF** — custom firewall rules (block/challenge/log) with presets.
- **Workers** — deploy Workers and manage routes from the panel.
- **Tunnels** — create Cloudflare Tunnels, copy the connector install
  command, and map public hostnames.
- **Storage** — R2 buckets, KV namespaces and D1 databases.

DNS records and the Cloudflare connection itself stay in the panel core (they
back `/domains`); this extension only adds the per-zone control panel.

## Install

[**Install in ServerKit →**](https://serverkit.ai/i/ext/serverkit-cloudflare-ops)

Or from the panel: **Marketplace → Extensions → Cloudflare Zone Ops**, or
upload a release zip via **Marketplace → Plugins → Upload Zip**.

## Development

```bash
cd frontend && npm install && npm run build   # dist/index.mjs (runtime-ESM)
./scripts/build-zip.sh                        # dist/serverkit-cloudflare-ops-<version>.zip
```

The frontend externalizes react / react-router-dom / i18next / serverkit-sdk —
the panel resolves them to its own singletons via its import map.

## Releasing

Bump `version` in `plugin.json` and push to `main` — the release workflow
builds the bundle, publishes the GitHub release, and updates the
`serverkit-extensions` registry entry from the published asset.

## License

MIT
