"""Core-hook registrations for Cloudflare Zone Ops (plan 86 §B4).

Registers an in-process listener for the core's ``app.deployed`` event, the
extension-to-core event path: on a successful deploy, zones with purge on
deploy switched on are purged for the deployed hostnames. Idempotent (the
core de-duplicates the listener) and torn down with the extension.

A panel without the listener API (older than this seam) simply never calls
it: purge on deploy is absent, everything else works.
"""
import logging

logger = logging.getLogger(__name__)

SLUG = 'serverkit-cloudflare-ops'


def on_app_deployed(payload):
    from .cloudflare_service import CloudflareService
    domains = (payload or {}).get('domains') or []
    if domains:
        CloudflareService.purge_for_deploy(domains)


def register():
    try:
        from app.services.event_service import register_listener
    except ImportError:
        logger.info('%s: panel has no event listener API; purge on deploy is off', SLUG)
        return
    register_listener('app.deployed', on_app_deployed, source=SLUG)
