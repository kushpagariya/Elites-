import html
import json
import base64
import hashlib
from io import BytesIO
from xml.sax.saxutils import escape

from .analytics import saved
from .sources import LIMITATIONS
from .errors import ServiceError
from ..repositories import store


def report_data(project_id, evaluation_id, portfolio_run_id=None):
    evaluation = saved(project_id, "evaluation", evaluation_id)
    context = saved(project_id, "evaluation_context", evaluation_id)
    portfolio = saved(project_id, "portfolio", portfolio_run_id) if portfolio_run_id else None
    if portfolio and portfolio["evaluation_id"] != evaluation_id:
        raise ServiceError(409, "CONTEXT_MISMATCH", "Portfolio does not belong to this evaluation.")
    frozen = store.get('report', project_id, report_key(evaluation_id, portfolio_run_id))
    if frozen:
        return frozen['data']
    return assemble(context, evaluation, portfolio,
                    saved(project_id, 'portfolio_context', portfolio_run_id)['request'] if portfolio else None)


def assemble(context, evaluation, portfolio, request):
    project = {key: value for key, value in context["project"].items() if key != "inputs"}
    inputs = context["project"]["inputs"]
    model = inputs.get("model_bundle")
    selected = set(portfolio["selected_site_ids"]) if portfolio else set()
    return {
        "project": project,
        "scenario": context["scenario"],
        "evaluation": evaluation,
        "portfolio": portfolio,
        "portfolio_request": request,
        "excluded_site_ids": [s["site_id"] for s in project["sites"] if s["site_id"] not in selected] if portfolio else [],
        "snapshot": context["snapshot"],
        "sources": inputs["source_manifest"],
        "infrastructure_evidence": inputs.get('infrastructure', []),
        "model_card": model["card"] if model else None,
        "limitations": [*evaluation.get('evidence', {}).get('limitations', LIMITATIONS), "A report records saved scenario assumptions, not guaranteed investment returns."],
    }


def render_html(data):
    """No executable content or interpolated raw HTML from data/model explanations."""
    evaluation = data["evaluation"]
    names = {s["site_id"]: s["name"] for s in data["project"]["sites"]}
    rows = []
    for item in evaluation["site_analyses"]:
        values = (names[item["site_id"]], item["annual_revenue_inr"], item["npv_inr"], item["roi_fraction"], item["payback_years"], item["failfast"]["status"])
        rows.append("<tr>" + "".join(f"<td>{html.escape('Unknown / not applicable' if value is None else str(value))}</td>" for value in values) + "</tr>")
    details = '<ul>' + ''.join('<li>' + html.escape(text) + '</li>' for text in data['limitations']) + '</ul>'
    identity = html.escape(evaluation["evaluation_id"])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>StoreScout saved decision report</title>
<style>body{{font:15px system-ui;margin:2rem auto;max-width:1100px;padding:0 1rem;color:#181818}}table{{width:100%;border-collapse:collapse}}th,td{{padding:.5rem;border:1px solid #ccc;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}}@media print{{body{{margin:0}}}}</style></head>
<body><h1>StoreScout saved decision report</h1><h2>{html.escape(data['scenario']['name'])}</h2><p>Evaluation: {identity}</p>
<p>Amounts are INR. Revenue is annual. ROI is a decimal fraction over the saved horizon, not IRR. Payback is years.</p>
<table><thead><tr><th>Candidate</th><th>Annual sales</th><th>Incremental NPV</th><th>Horizon ROI fraction</th><th>Payback</th><th>Diagnosis</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Risks and assumptions</h2>{details}</body></html>"""


def report_key(evaluation_id, portfolio_run_id):
    return evaluation_id + ':' + (portfolio_run_id or 'analysis')


def pdf_bytes(document):
    content = base64.b64decode(document['pdf_base64'])
    if hashlib.sha256(content).hexdigest() != document['sha256']:
        raise ServiceError(503, 'REPORT_INTEGRITY', 'The saved report failed its integrity check.')
    return content


def freeze(context, evaluation, portfolio, request):
    """Render once with saved evidence, persisted atomically with the plan."""
    data = assemble(context, evaluation, portfolio, request)
    content = render_pdf(data)
    return dict(data=data, pdf_base64=base64.b64encode(content).decode('ascii'),
                sha256=hashlib.sha256(content).hexdigest(),
                filename=f'storescout-bengaluru-{evaluation["evaluation_id"]}-{portfolio["portfolio_run_id"]}.pdf',
                renderer='storescout-decision-pdf-1')


def pdf_document(project_id, evaluation_id, portfolio_run_id):
    data = report_data(project_id, evaluation_id, portfolio_run_id)  # authorise both saved identities first
    if not portfolio_run_id:
        raise ServiceError(422, 'PORTFOLIO_REQUIRED', 'Choose a saved investment plan for the decision PDF.')
    identity = report_key(evaluation_id, portfolio_run_id)
    document = store.get('report', project_id, identity)
    if document is None:
        # Legacy plans predate PDF storage. Freeze their saved evidence on first export.
        context = saved(project_id, 'evaluation_context', evaluation_id)
        document = freeze(context, data['evaluation'], data['portfolio'], data['portfolio_request'])
        winner = store.save_result(project_id, 'report', identity, None, identity, identity,
                                  [('report', identity, document)])
        document = saved(project_id, 'report', winner)
    return document


def money(value):
    if value is None:
        return 'Not available'
    # Plain INR is portable and avoids missing rupee glyphs in standard PDF fonts.
    return f'INR {value:,.0f}'


def render_pdf(data):
    """Human decision document. No model loading, new valuation or raw JSON."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.graphics.shapes import Drawing, Rect, String, Line

    ink, green, muted = colors.HexColor('#183E35'), colors.HexColor('#21816A'), colors.HexColor('#56645F')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CoverTitle', fontName='Helvetica-Bold', fontSize=30, leading=35, textColor=ink, spaceAfter=16))
    styles.add(ParagraphStyle(name='Deck', fontSize=12, leading=18, textColor=muted, spaceAfter=15))
    styles['BodyText'].fontSize = 9
    styles['BodyText'].leading = 12
    styles['BodyText'].spaceAfter = 5
    styles['Heading2'].textColor = ink
    styles['Heading2'].spaceBefore = 15
    styles['Heading2'].spaceAfter = 10
    styles.add(ParagraphStyle(name='SmallNote', fontSize=7.5, leading=11, textColor=muted, spaceAfter=6))
    styles.add(ParagraphStyle(name='TableCell', fontSize=8, leading=11, alignment=TA_LEFT))
    p = lambda text, style='BodyText': Paragraph(escape(str(text)).replace('\n', '<br/>'), styles[style])
    story = []
    e, plan, scenario, project = data['evaluation'], data['portfolio'], data['scenario'], data['project']
    names = {s['site_id']: s['name'] for s in project['sites']}
    selected = set(plan['selected_site_ids']) if plan else set()
    analyses = {a['site_id']: a for a in e['site_analyses']}
    horizon = project['projection_years']

    def table(rows, widths, header=True):
        value = Table([[p(c, 'TableCell') for c in row] for row in rows], colWidths=widths, repeatRows=1 if header else 0, hAlign='LEFT')
        value.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E6EFEA')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
            ('LINEBELOW', (0, 0), (-1, -1), .35, colors.HexColor('#DCE4DF'))]))
        return value

    story += [p('STORESCOUT / BENGALURU GROCERY', 'SmallNote'), Spacer(1, 10),
              p('Your expansion\ndecision', 'CoverTitle'),
              p(scenario['name'], 'Deck'),
              p('Saved analysis: ' + e['created_at_utc'][:10] + f' | {horizon}-year horizon | Synthetic-trained model', 'SmallNote')]
    story.append(p('Recommendation', 'Heading2'))
    if selected:
        recommendation = 'Review ' + ', '.join(names[sid] for sid in plan['selected_site_ids']) + ' for the next stage of due diligence.'
    else:
        recommendation = 'Keep the expansion budget uncommitted under these saved eligibility, risk and budget settings.'
    if plan and plan['status'] != 'FULL_NETWORK_EXACT':
        recommendation += ' The search was incomplete; this is a feasible plan, not a proven best combination.'
    story += [p(recommendation, 'Deck'),
              p('This is a modelled planning recommendation, not investment approval. All commercial assumptions and remaining location risks require review.')]
    if plan:
        story.append(table([
            ['Expansion budget', 'Proposed investment', f'{horizon}-year network NPV'],
            [money(scenario['budget_inr']), money(plan['budget_used_inr']), money(plan['full_network_npv_inr'])]], [170, 170, 171]))
        story.append(Spacer(1, 18))
        budget = max(scenario['budget_inr'], 1)
        chart = Drawing(510, 63)
        chart.add(Rect(0, 25, 510, 16, fillColor=colors.HexColor('#E6EFEA'), strokeColor=None))
        chart.add(Rect(0, 25, 510 * min(plan['budget_used_inr']/budget, 1), 16, fillColor=green, strokeColor=None))
        chart.add(String(0, 8, 'Invested: ' + money(plan['budget_used_inr']), fontSize=9, fillColor=ink))
        chart.add(String(510, 8, 'Remaining: ' + money(plan['budget_unused_inr']), textAnchor='end', fontSize=9, fillColor=ink))
        story.append(chart)
    story.append(p('Selected locations', 'Heading2'))
    for sid in plan['selected_site_ids'] if plan else []:
        a = analyses[sid]
        story.append(KeepTogether([p(names[sid] + ' / ' + a['failfast']['status'].replace('_', ' ')),
                                  p('Opened alone: annual sales ' + money(a['annual_revenue_inr']) + '; incremental NPV ' + money(a['npv_inr']) + '.', 'SmallNote')]))
    if not selected:
        story.append(p('No candidates selected. An empty portfolio is a valid result.'))
    story.append(p('Combined portfolio NPV is calculated jointly with overlap and existing-branch impact. Individual estimates below must not be summed into a network total.', 'SmallNote'))

    story += [PageBreak(), p('Financial comparison', 'CoverTitle'),
              p('Each row models a single location opening alone. Annual sales and operating profit refer to year one; NPV and ROI cover the saved horizon.', 'BodyText')]
    rows = [['Location', 'Annual sales', 'Operating profit', 'Incremental NPV', 'Horizon ROI', 'Risk status']]
    for site in project['sites']:
        a = analyses[site['site_id']]
        rows.append([site['name'] + (' *' if site['site_id'] in selected else ''), money(a['annual_revenue_inr']),
                     money(a.get('operating_profit_inr')), money(a['npv_inr']),
                     f"{a['roi_fraction']*100:,.1f}%" if a.get('roi_fraction') is not None else 'Not applicable',
                     a['failfast']['status'].replace('_', ' ')])
    story += [table(rows, [100, 86, 86, 91, 65, 83]), p('* Selected in the saved portfolio. Operating profit excludes existing-branch displacement; incremental NPV includes it and initial investment.', 'SmallNote')]
    story.append(p('Single-location incremental NPV', 'Heading2'))
    chart = Drawing(510, 215)
    max_abs = max([abs(a['npv_inr']) for a in analyses.values()] + [1])
    chart.add(Line(300, 10, 300, 210, strokeColor=colors.HexColor('#C7D4CE')))
    for index, site in enumerate(project['sites']):
        y = 198-index*19
        npv = analyses[site['site_id']]['npv_inr']
        length = 190*abs(npv)/max_abs
        chart.add(String(0, y, site['name'][:33], fontSize=8, fillColor=ink))
        chart.add(Rect(300 if npv >= 0 else 300-length, y-2, max(length,.5), 9,
                       fillColor=green if npv >= 0 else colors.HexColor('#B64E3E'), strokeColor=None))
    story += [chart, p('Bars use a shared scale centred at zero. Exact amounts are in the comparison table.', 'SmallNote'), PageBreak()]
    story += [p('Risks & assumptions', 'CoverTitle'),
              p('What must be checked before a real investment', 'Deck')]
    assumptions = scenario['assumptions']
    story.append(table([
        ['Saved assumption', 'Value / interpretation'],
        ['Area-wide demand', f"{assumptions['demand_multiplier']:.3f}x baseline wallet and demand"],
        ['Area-wide rent', f"{assumptions['rent_multiplier']:.3f}x each location's base monthly rent"],
        ['Discount rate / horizon', f"{project['discount_rate_fraction']*100:.1f}% / {horizon} years"],
        ['Infrastructure', assumptions['infrastructure_state'].title() + f"; commercial effect {assumptions['infrastructure_effect_fraction']*100:.1f}% (assumed)"],
        ['Opening timing', 'Assumed opening ' + str(assumptions.get('opening_date') or 'source scenario date') + f"; delay {assumptions['delay_months']} months when Delayed is selected"],
    ], [150, 361]))
    for sid, override in assumptions['site_overrides'].items():
        values = []
        if override.get('monthly_rent_inr') is not None:
            values.append('base rent ' + money(override['monthly_rent_inr']) + '/month')
        if override.get('sales_multiplier') is not None:
            values.append(f"sales adjustment {override['sales_multiplier']:.3f}x baseline")
        if values:
            story.append(p(names[sid] + ': ' + '; '.join(values), 'SmallNote'))
    for event in data.get('infrastructure_evidence', []):
        assumed = assumptions.get('opening_date') or event.get('assumed_demo_open_date') or event.get('expected_open_date')
        exposures = [x for a in e['site_analyses'] for x in a.get('infrastructure_exposure', []) if x['event_id']==event['infra_project_id']]
        effective = exposures[0]['opening_date'] if exposures else None
        story.append(p(event['name'] + ': assumed opening ' + str(assumed or 'unknown') + '; effective scenario opening ' + str(effective or 'not activated') + '. ' + event.get('geometry_note', ''), 'SmallNote'))
    story.append(p('Location risks', 'Heading2'))
    review_ids = plan['selected_site_ids'] if selected else list(analyses)
    unique_risks = list(dict.fromkeys(reason for sid in review_ids for reason in analyses[sid]['failfast']['reasons']))
    labels = {
        '100_CELL_CENTROID_APPROXIMATION':'Demand is represented by 100 cell centres rather than individual households.',
        'ASSUMED_EQUAL_COMPETITOR_ATTRACTION':'Mapped competitors are assigned equal attraction; shop performance is not observed.',
        'HCES_STATE_URBAN_SPENDING_2023_24':'Household spending uses a historical state-urban proxy, not local current spending.',
        'HISTORICAL_MODELLED_POPULATION_2020':'Population estimates are modelled for 2020.',
        'NOMINAL_WALLET_2024_VS_SYNTHETIC_COSTS_2026':'Historical spending and assumed current costs use different price periods.',
        'OSM_PARTIAL_COVERAGE':'OpenStreetMap shop and destination coverage is incomplete.',
        'SHIFTED_MARKET_DEGRADATION_REVIEW':'The fitted model performs worse on shifted synthetic markets; human review is required.',
        'SYNTHETIC_MODEL_NO_REAL_OUTCOME_VALIDATION':'The model has not been validated against actual store sales.',
    }
    status_counts = {status: sum(analyses[sid]['failfast']['status']==status for sid in review_ids)
                     for status in sorted({analyses[sid]['failfast']['status'] for sid in review_ids})}
    story.append(p('Locations reviewed: ' + '; '.join(f'{count} {status.replace("_", " ").lower()}' for status,count in status_counts.items()) + '. Shared model, source and commercial risks are explained below.'))
    for risk in unique_risks:
        if risk not in labels:
            story.append(p('- ' + risk.replace('_', ' ')))
    story.append(p('Evidence limitations', 'Heading2'))
    for text in dict.fromkeys(data['limitations']):
        story.append(p('- ' + text))
    story.append(p('Sources and decision record', 'Heading2'))
    story.append(p('OpenStreetMap mapped shops and destinations; modelled WorldPop 2020 population; HCES 2023-24 Karnataka urban spending proxy. Rents, costs, store sizes and four existing branches are assumed/synthetic. No observed store sales validate this prototype.'))
    source_manifest = data.get('sources', {})
    source_records = source_manifest.get('sources', []) if isinstance(source_manifest, dict) else []
    if isinstance(source_records, list):
        for source in source_records:
            if isinstance(source, dict):
                label = source.get('name') or source.get('source_id')
                url = source.get('url') or source.get('source_url')
                if label and url:
                    story.append(p(str(label) + ': ' + str(url), 'SmallNote'))
    story.append(p('Saved evaluation: ' + e['evaluation_id'] + '\nSaved portfolio: ' + (plan['portfolio_run_id'] if plan else 'None') + '\nModel: ' + str(e.get('model_artifact_id')) + '\nThis PDF is stored with its saved evidence and is not recalculated when opened.', 'SmallNote'))

    class NumberedCanvas(Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.saved_pages = []
        def showPage(self):
            self.saved_pages.append(dict(self.__dict__))
            self._startPage()
        def save(self):
            total = len(self.saved_pages)
            for page in self.saved_pages:
                self.__dict__.update(page)
                self.setFillColor(muted)
                self.setFont('Helvetica', 8)
                self.drawString(16*mm, 12*mm, 'StoreScout | Bengaluru grocery | Modelled planning case')
                self.drawRightString(194*mm, 12*mm, f'Page {self._pageNumber} of {total}')
                super().showPage()
            super().save()

    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=(210*mm, 297*mm), rightMargin=16*mm, leftMargin=16*mm,
                                 topMargin=17*mm, bottomMargin=22*mm, title='StoreScout Bengaluru decision report',
                                 author='StoreScout', invariant=1)
    document.build(story, canvasmaker=NumberedCanvas)
    return output.getvalue()
