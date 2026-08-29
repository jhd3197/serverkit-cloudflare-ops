// Runtime-ESM entry for ServerKit's no-rebuild loader (same pattern as
// serverkit-wordpress). The SCSS compiles at extension build time (sass) and
// is imported as a STRING (?inline), then injected once at module load — the
// single dist/index.mjs the panel blob-imports carries its own styles. Shared
// libs (react, react-router-dom, i18next, serverkit-sdk) are externalized by
// vite.config and resolved to the panel's singletons via its import map.
import css0 from './styles/cloudflare-zone.scss?inline';

if (typeof document !== 'undefined' && !document.getElementById('serverkit-cloudflare-ops-styles')) {
    const style = document.createElement('style');
    style.id = 'serverkit-cloudflare-ops-styles';
    style.textContent = css0;
    document.head.appendChild(style);
}

// Translations — registered against the PANEL's i18next singleton (shared via
// its vendor import map), additively; never init() or changeLanguage(), which
// the panel owns. Keys keep their historical app.* paths, so a panel that
// still carries them in core simply sees identical values.
import i18next from 'i18next';
import en from './locales/en.json';
import es from './locales/es.json';

for (const [language, bundle] of Object.entries({ en, es })) {
    i18next.addResourceBundle(language, 'translation', bundle, true, false);
}

// Named exports match the `component` values in plugin.json's route
// contributions; resolveComponent(slug, name) picks them up at runtime.
// Deliberately NO default export (PluginLoader auto-renders those globally).
export { CloudflareZoneSettingsPage } from './index.jsx';
