"""Cache Rules presets and purge on deploy (plan 86 §B4).

Run from the panel's venv so ``app`` (the panel backend) imports:

    SERVERKIT_BACKEND=../ServerKit/backend python -m pytest tests

The extension is loaded as a package, the way the panel loads it.
"""
import importlib.util
import os
import sys
from types import SimpleNamespace

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.environ.get('SERVERKIT_BACKEND') or os.path.join(HERE, '..', '..', 'ServerKit', 'backend')
sys.path.insert(0, os.path.abspath(BACKEND))


def _load():
    pkg_dir = os.path.join(HERE, '..', 'backend')
    spec = importlib.util.spec_from_file_location(
        'cf_ops', os.path.join(pkg_dir, '__init__.py'), submodule_search_locations=[pkg_dir])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules['cf_ops'] = pkg
    spec.loader.exec_module(pkg)
    return (importlib.import_module('cf_ops.cloudflare_service'),
            importlib.import_module('cf_ops.core_hooks'))


svc_mod, hooks = _load()
CS = svc_mod.CloudflareService


def test_the_cache_phase_is_a_rule_type():
    assert CS._resolve_rule_phase('cache') == 'http_request_cache_settings'
    CS._validate_rule_action('cache', 'set_cache_settings')
    with pytest.raises(svc_mod.CloudflareError):
        CS._validate_rule_action('cache', 'redirect')
    assert {p['key'] for p in CS.RULE_PRESETS['cache']} == {'cache_static', 'bypass_api_admin'}


def test_cache_static_respects_the_origin_lifetime():
    rule = CS._build_rule_preset('cache', 'cache_static', 'example.com', {})
    assert rule['action'] == 'set_cache_settings'
    assert rule['expression'].startswith('(http.request.uri.path.extension in {"js"')
    assert rule['action_parameters'] == {'cache': True,
                                         'edge_ttl': {'mode': 'respect_origin'},
                                         'browser_ttl': {'mode': 'respect_origin'}}


def test_bypass_covers_api_and_admin_paths():
    rule = CS._build_rule_preset('cache', 'bypass_api_admin', 'example.com', {})
    assert rule['action_parameters'] == {'cache': False}
    for path in ('/api', '/admin', '/wp-admin', '/login'):
        assert f'"{path}"' in rule['expression']


def test_the_most_specific_zone_wins():
    zones = [SimpleNamespace(id=1, domain='example.com'),
             SimpleNamespace(id=2, domain='shop.example.com')]
    assert CS._zone_for_host(zones, 'shop.example.com').id == 2
    assert CS._zone_for_host(zones, 'api.shop.example.com').id == 2
    assert CS._zone_for_host(zones, 'blog.example.com').id == 1
    assert CS._zone_for_host(zones, 'notexample.com') is None


def test_purge_on_deploy_hits_only_opted_in_zones(monkeypatch):
    zones = [SimpleNamespace(id=1, domain='example.com'),
             SimpleNamespace(id=2, domain='other.org')]
    stored = {'purge_on_deploy:1': True}
    monkeypatch.setattr(CS, '_store', staticmethod(lambda: SimpleNamespace(get=stored.get)))
    fake_model = SimpleNamespace(query=SimpleNamespace(filter=lambda *a: SimpleNamespace(all=lambda: zones)),
                                 provider=None)
    monkeypatch.setitem(sys.modules, 'app.models.dns_zone', SimpleNamespace(DNSZone=fake_model))
    purged = []
    monkeypatch.setattr(CS, 'purge_cache', classmethod(
        lambda cls, zone_id, hosts=None: purged.append((zone_id, hosts)) or {'success': True}))

    CS.purge_for_deploy(['Shop.Example.com', 'www.other.org', 'unrelated.net'])

    assert purged == [(1, ['shop.example.com'])]


def test_a_failed_purge_never_raises(monkeypatch):
    zones = [SimpleNamespace(id=1, domain='example.com')]
    monkeypatch.setattr(CS, '_store', staticmethod(lambda: SimpleNamespace(get=lambda k: True)))
    fake_model = SimpleNamespace(query=SimpleNamespace(filter=lambda *a: SimpleNamespace(all=lambda: zones)),
                                 provider=None)
    monkeypatch.setitem(sys.modules, 'app.models.dns_zone', SimpleNamespace(DNSZone=fake_model))

    def boom(cls, zone_id, hosts=None):
        raise RuntimeError('network down')
    monkeypatch.setattr(CS, 'purge_cache', classmethod(boom))
    assert CS.purge_for_deploy(['example.com'])[1]['success'] is False


def test_core_hooks_listens_for_app_deployed(monkeypatch):
    registered = []
    fake = SimpleNamespace(register_listener=lambda event, fn, source=None:
                           registered.append((event, fn, source)))
    monkeypatch.setitem(sys.modules, 'app.services.event_service', fake)
    hooks.register()
    assert registered == [('app.deployed', hooks.on_app_deployed, 'serverkit-cloudflare-ops')]
