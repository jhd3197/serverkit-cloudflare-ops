import { useCallback, useEffect, useState } from 'react';
import api from '../services/cloudflare';
import { Button, Badge, EmptyState, useToast } from 'serverkit-sdk';
import { useTranslation } from 'react-i18next';

// Redirect, Transform and Cache Rules (plan 86 §B4): one ruleset per phase,
// applied from presets that interpolate nothing but the zone's own domain.
// Cache Rules sit next to the other two because they are the same machinery.
const PHASES = ['cache', 'redirect', 'transform'];

function PhaseSection({ zoneId, phase, isAdmin }) {
    const { t } = useTranslation();
    const toast = useToast();
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [busy, setBusy] = useState(null);

    const load = useCallback(async () => {
        try {
            setData(await api.getCloudflareRules(zoneId, phase));
            setError(null);
        } catch (err) {
            setError(err.message);
        }
    }, [zoneId, phase]);

    useEffect(() => { load(); }, [load]);

    async function applyPreset(key) {
        setBusy(key);
        try {
            await api.applyCloudflareRulePreset(zoneId, phase, key);
            toast.success(t('app.cloudflareRulesPanel.ruleAdded', 'Rule added'));
            await load();
        } catch (err) {
            toast.error(err.message);
        } finally {
            setBusy(null);
        }
    }

    async function remove(rule) {
        setBusy(rule.id);
        try {
            await api.deleteCloudflareRule(zoneId, phase, data.ruleset_id, rule.id);
            await load();
        } catch (err) {
            toast.error(err.message);
        } finally {
            setBusy(null);
        }
    }

    return (
        <section className="cf-waf__section">
            <h3 className="cf-waf__heading">{{
                cache: t('app.cloudflareRulesPanel.cacheRules', 'Cache Rules'),
                redirect: t('app.cloudflareRulesPanel.redirectRules', 'Redirect Rules'),
                transform: t('app.cloudflareRulesPanel.transformRules', 'Transform Rules'),
            }[phase]}</h3>
            {error && <p className="cf-waf__hint">{error}</p>}
            {data && (
                <>
                    <div className="cf-rules__presets">
                        {data.presets.map((preset) => (
                            <div key={preset.key} className="cf-rules__preset">
                                <div>
                                    <strong>{preset.label}</strong>
                                    <p className="cf-waf__preset-desc">{preset.description}</p>
                                </div>
                                <Button size="sm" variant="outline" disabled={!isAdmin || busy === preset.key}
                                    onClick={() => applyPreset(preset.key)}>
                                    {t('app.cloudflareRulesPanel.add', 'Add')}
                                </Button>
                            </div>
                        ))}
                    </div>
                    {data.rules.length ? (
                        <ul className="cf-rules__list">
                            {data.rules.map((rule) => (
                                <li key={rule.id} className="cf-rules__rule">
                                    <span>{rule.description}</span>
                                    {!rule.enabled && <Badge variant="outline">{t('app.cloudflareRulesPanel.off', 'Off')}</Badge>}
                                    <Button size="sm" variant="ghost" disabled={!isAdmin || busy === rule.id}
                                        onClick={() => remove(rule)}>
                                        {t('app.cloudflareRulesPanel.remove', 'Remove')}
                                    </Button>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <EmptyState
                            title={t('app.cloudflareRulesPanel.noRules', 'No rules yet')}
                            description={t('app.cloudflareRulesPanel.noRulesHint', 'Add one of the presets above.')}
                        />
                    )}
                </>
            )}
        </section>
    );
}

export default function RulesPanel({ zoneId, isAdmin }) {
    return (
        <div className="cf-waf">
            {PHASES.map((phase) => (
                <PhaseSection key={phase} zoneId={zoneId} phase={phase} isAdmin={isAdmin} />
            ))}
        </div>
    );
}
