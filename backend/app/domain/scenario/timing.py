"""One dated infrastructure bridge. No second inference or duplicate uplift."""
import calendar
from datetime import date
import numpy as np
from ..geospatial.features import distances
from ..validation import DomainUnavailable, number


def add_months(day, months):
    month = day.month - 1 + months
    year, month = day.year + month // 12, month % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def active_fractions(valuation_date, opening_date, years):
    start, opening = date.fromisoformat(valuation_date), date.fromisoformat(opening_date)
    output = []
    for year in range(years):
        a, b = add_months(start, 12 * year), add_months(start, 12 * (year + 1))
        output.append(max(0., min(1., (b - max(a, opening)).days / (b-a).days)))
    return output


def infrastructure_multipliers(sites, events, assumptions, valuation_date, years):
    state = assumptions.get('infrastructure_state', 'current')
    if state not in ('current', 'opens', 'delayed'):
        raise ValueError('Unknown infrastructure state')
    effect = number(assumptions.get('infrastructure_effect_fraction', 0.), 'infrastructure effect', minimum=-1, maximum=2)
    if len(events) > 1:
        raise ValueError('P0 supports one explicitly selected infrastructure event')
    multipliers = np.ones((years, len(sites)))
    evidence = []
    for event in events:
        status = event['status'].lower()
        if status not in ('proposed', 'approved', 'funded', 'under_construction', 'operational', 'delayed', 'cancelled', 'unknown'):
            raise ValueError('Unsupported infrastructure status')
        if status in ('operational', 'cancelled') or state == 'current':
            evidence.append(dict(event_id=event['infra_project_id'], status=status,
                                 treatment='ALREADY_IN_BASELINE' if status == 'operational' else 'INACTIVE'))
            continue
        geometry = event.get('geometry')
        opening = assumptions.get('opening_date') or event.get('expected_open_date')
        if not opening and event.get('hypothetical_demo'):
            opening = event.get('assumed_demo_open_date')
        if not opening or not geometry or geometry.get('type') != 'Point':
            raise DomainUnavailable('Future event requires explicit ISO opening date and supported Point geometry')
        if status == 'unknown' and not event.get('hypothetical_demo'):
            raise DomainUnavailable('Unknown infrastructure status requires explicit hypothetical evidence')
        point = dict(longitude=geometry['coordinates'][0], latitude=geometry['coordinates'][1])
        exposure = np.exp(-distances(sites, [point])[:, 0] / 750.)
        if state == 'delayed':
            delay = assumptions.get('delay_months', 24)
            if isinstance(delay, bool) or not isinstance(delay, int) or not 0 <= delay <= 120:
                raise ValueError('Invalid infrastructure delay months')
            opening = add_months(date.fromisoformat(opening), delay).isoformat()
        fractions = active_fractions(valuation_date, opening, years)
        multipliers += np.asarray(fractions)[:, None] * exposure[None, :] * effect
        evidence.append(dict(event_id=event['infra_project_id'], status=status, opening_date=opening,
                             active_fractions=fractions, exposure=exposure.tolist(), effect_fraction=effect,
                             source_id=event.get('source_id'), hypothetical=bool(event.get('hypothetical_demo')),
                             interpretation='ASSUMED commercial effect from proximity, not measured accessibility improvement'))
    if np.any(multipliers < 0):
        raise ValueError('Infrastructure target must remain nonnegative')
    return multipliers, evidence
