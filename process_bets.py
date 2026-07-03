#!/usr/bin/env python3
"""
process_bets.py — PIC Bet Log Processor
Reads bets_log.json → updates PIC_Dashboard.html + PIC_2026_Tracker.xlsx → clears log.
Run this before pushing to GitHub (push.bat does it automatically).
"""

import json, re, sys, os
from pathlib import Path
from datetime import datetime

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False
    print("⚠  openpyxl not installed — spreadsheet will NOT be updated.")
    print("   Install with: pip install openpyxl --break-system-packages")

FOLDER = Path(__file__).parent
HTML_F = FOLDER / "PIC_Dashboard.html"
XLSX_F = FOLDER / "PIC_2026_Tracker.xlsx"
LOG_F  = FOLDER / "bets_log.json"

CAPTAINS       = ['Charlie', 'Shannon', 'Douchie', 'Nic']
SAVINGS_WEEKLY = 30.0   # each captain's weekly pool contribution


# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────

def month_of(d):
    """'20 Jun 2026' → 'Jun'"""
    p = d.strip().split()
    return p[1] if len(p) >= 3 else '?'

def wr_pct(wins, n):
    return f'{round(wins / n * 100)}%' if n else '0%'

def nsign(v):
    return '+' if v >= 0 else ''

def nc(v):
    """net CSS class"""
    return 'net-positive' if v >= 0 else 'net-negative'

def pc(v):
    """positive/negative CSS class"""
    return 'positive' if v >= 0 else 'negative'

def fmtd(v, signed=False):
    """Format as dollar.  signed=True → '+$56.40' / '-$56.40'"""
    s = f'${abs(v):,.2f}'
    if signed:
        s = ('+' if v >= 0 else '-') + s
    return s

def today_str():
    return datetime.now().strftime('%-d %b %Y').lstrip('0') if os.name != 'nt' \
        else datetime.now().strftime('%#d %b %Y')


# ─────────────────────────────────────────────────────────────────────────────
# Parse existing bet rows from a captain's HTML section
# ─────────────────────────────────────────────────────────────────────────────

BET_ROW_RE = re.compile(
    r'<tr><td><span class="month-badge">\w+</span>([^<]+)</td>'
    r'<td>(.*?)</td>'
    r'<td>(.*?)</td>'
    r'<td class="monospace">\$([\d,.]+)</td>'
    r'<td class="monospace">\$([\d,.]+)</td>'
    r'<td><span class="badge badge-(\w+)">[^<]+</span></td>'
    r'<td class="monospace[^"]*">[^<]*</td></tr>',
    re.DOTALL
)

def parse_bets(section_html):
    bets = []
    for m in BET_ROW_RE.finditer(section_html):
        date, desc, odds, stake_s, ret_s, res_word = m.groups()
        bets.append({
            'date':   date.strip(),
            'desc':   desc.strip(),
            'odds':   odds.strip() or '—',
            'stake':  float(stake_s.replace(',', '')),
            'return': float(ret_s.replace(',', '')),
            'result': 'Win' if res_word == 'win' else 'Loss',
        })
    return bets

def stats(bets):
    staked = sum(b['stake']  for b in bets)
    ret    = sum(b['return'] for b in bets)
    wins   = sum(1 for b in bets if b['result'] == 'Win')
    losses = sum(1 for b in bets if b['result'] == 'Loss')
    n      = len(bets)
    return dict(staked=staked, ret=ret, net=ret - staked,
                wins=wins, losses=losses, n=n, wr=wr_pct(wins, n))


# ─────────────────────────────────────────────────────────────────────────────
# Build HTML fragments
# ─────────────────────────────────────────────────────────────────────────────

def desktop_row(b):
    mo  = month_of(b['date'])
    st  = b['stake']
    rt  = b['return']
    net = rt - st
    odds = b.get('odds', '—') or '—'
    res  = b['result']
    return (
        f'      <tr><td><span class="month-badge">{mo}</span>{b["date"]}</td>'
        f'<td>{b["desc"]}</td><td>{odds}</td>'
        f'<td class="monospace">${st:.2f}</td>'
        f'<td class="monospace">${rt:.2f}</td>'
        f'<td><span class="badge badge-{res.lower()}">{res}</span></td>'
        f'<td class="monospace {nc(net)}">{nsign(net)}${abs(net):.2f}</td></tr>\n'
    )

def mobile_card(b):
    res = b['result']
    st  = b['stake']
    rt  = b['return']
    net = rt - st
    col = 'var(--green)' if net >= 0 else 'var(--red)'
    odds = b.get('odds', '—') or '—'
    parts = []
    if odds != '—':
        parts.append(f'<div class="bet-card-stat"><strong>{odds}</strong>Odds</div>')
    if res == 'Win':
        parts.append(f'<div class="bet-card-stat"><strong>${rt:.2f}</strong>Return</div>')
        parts.append(f'<div class="bet-card-stat" style="color:{col}"><strong style="color:{col}">{nsign(net)}${abs(net):.2f}</strong>Net</div>')
    else:
        if abs(st - 30) > 0.01:
            parts.append(f'<div class="bet-card-stat"><strong>${st:.2f}</strong>Stake</div>')
        parts.append(f'<div class="bet-card-stat" style="color:{col}"><strong style="color:{col}">{nsign(net)}${abs(net):.2f}</strong>Net</div>')
    return (
        f'    <div class="bet-card {res.lower()}">'
        f'<div class="bet-card-top"><span class="bet-card-date">{b["date"]}</span>'
        f'<span class="badge badge-{res.lower()}">{res}</span></div>'
        f'<div class="bet-card-desc">{b["desc"]}</div>'
        f'<div class="bet-card-row">{"".join(parts)}</div></div>\n'
    )

def totals_row_html(s):
    return (
        f'      <tr class="totals-row"><td colspan="3"><strong>TOTAL</strong></td>'
        f'<td class="monospace"><strong>{fmtd(s["staked"])}</strong></td>'
        f'<td class="monospace"><strong>{fmtd(s["ret"])}</strong></td>'
        f'<td></td>'
        f'<td class="monospace {nc(s["net"])}"><strong>{fmtd(s["net"], signed=True)}</strong></td></tr>\n'
    )

def cards_total_html(s):
    return (
        f'    <div class="bet-cards-total">'
        f'<span>Total · {s["n"]} bets · {s["wins"]}W {s["losses"]}L</span>'
        f'<span class="{nc(s["net"])}">{fmtd(s["net"], signed=True)}</span></div>\n'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Captain section updater
# ─────────────────────────────────────────────────────────────────────────────

def update_captain_section(sec, new_bets):
    """Add new bets to a captain's HTML section and recalculate stats."""
    existing = parse_bets(sec)
    all_bets = existing + new_bets
    s        = stats(all_bets)

    if not new_bets:
        return sec, s

    # 1. Insert desktop rows before totals row
    new_rows = ''.join(desktop_row(b) for b in new_bets)
    sec = sec.replace(
        '      <tr class="totals-row">',
        new_rows + '      <tr class="totals-row">'
    )

    # 2. Replace totals row
    sec = re.sub(
        r'      <tr class="totals-row">.*?</tr>\n',
        totals_row_html(s),
        sec, flags=re.DOTALL
    )

    # 3. Insert mobile cards before bet-cards-total
    new_cards = ''.join(mobile_card(b) for b in new_bets)
    sec = sec.replace(
        '    <div class="bet-cards-total">',
        new_cards + '    <div class="bet-cards-total">'
    )

    # 4. Replace bet-cards-total
    sec = re.sub(
        r'    <div class="bet-cards-total">.*?</div>\n',
        cards_total_html(s),
        sec, flags=re.DOTALL
    )

    # 5. Bet count in sub-header
    sec = re.sub(
        r'(#\d+) · \d+ Bets · 2026 Season',
        lambda m: f"{m.group(1)} · {s['n']} Bets · 2026 Season",
        sec
    )

    # 6. Bettor-stat values in header
    def repl_stat(label, val):
        nonlocal sec
        sec = re.sub(
            rf'(<div class="bettor-stat-label">{re.escape(label)}</div>'
            rf'<div class="bettor-stat-value[^"]*">)[^<]+',
            lambda m: m.group(1) + val,
            sec
        )

    repl_stat('Staked',   fmtd(s['staked']))
    repl_stat('Return',   fmtd(s['ret']))
    repl_stat('Win Rate', s['wr'])

    # Net P&L has a dynamic class
    sec = re.sub(
        r'<div class="bettor-stat-label">Net P&amp;L</div>'
        r'<div class="bettor-stat-value[^"]*">[^<]+',
        f'<div class="bettor-stat-label">Net P&amp;L</div>'
        f'<div class="bettor-stat-value {pc(s["net"])}">{fmtd(s["net"], signed=True)}',
        sec
    )

    return sec, s


# ─────────────────────────────────────────────────────────────────────────────
# Rank captains
# ─────────────────────────────────────────────────────────────────────────────

STRIPE_COLORS = {'1': '#0D1B2A', '2': '#555', '3': '#8B5E1A', '4': '#999'}

def rank_captains(all_stats):
    """Return {captain: rank_int} ranked by net P&L descending."""
    ordered = sorted(CAPTAINS, key=lambda c: -all_stats[c]['net'])
    return {c: i + 1 for i, c in enumerate(ordered)}


def update_bettor_rank(sec, new_rank):
    """Replace #N in the bettor sub-header of a captain section."""
    return re.sub(
        r'#\d+( · \d+ Bets · 2026 Season)',
        lambda m: f'#{new_rank}{m.group(1)}',
        sec
    )


# ─────────────────────────────────────────────────────────────────────────────
# Leaderboard rebuild
# ─────────────────────────────────────────────────────────────────────────────

def outstanding_badge(captain, sched_html):
    """Count unlogged future/past weeks in SCHEDULE for this captain."""
    # Parse SCHEDULE from JS
    entries = re.findall(
        rf"\{{ date: '([^']+)', captain: '{captain}',\s+logged: (false|true)(?:,\s+noBet: true)?\s*\}}",
        sched_html
    )
    # Count where logged=false AND date is not in the future (i.e. should have been played)
    today = datetime.now()
    overdue = 0
    for date_s, logged in entries:
        if logged == 'false':
            try:
                dt = datetime.strptime(date_s, '%d %b %Y')
                if dt <= today:
                    overdue += 1
            except ValueError:
                pass
    if overdue == 0: return ''
    if overdue == 1: return '⚠ BET OUTSTANDING'
    return f'⚠ {overdue} BETS OUTSTANDING'


def build_lb_card(captain, rank, s, badge):
    pnl_c  = pc(s['net'])
    net_str = fmtd(s['net'], signed=True)
    badge_html = (
        f' &nbsp;<span style="background:#FEF3C7;color:#B45309;font-size:11px;'
        f'font-weight:700;padding:2px 8px;border-radius:12px;letter-spacing:1px">'
        f'{badge}</span>'
    ) if badge else ''
    record = f'{s["wins"]}W &nbsp;{s["losses"]}L &nbsp;·&nbsp; {s["n"]} Bets{badge_html}'
    color  = STRIPE_COLORS.get(str(rank), '#888')
    cap_l  = captain.lower()
    return (
        f'    <div class="lb-card" onclick="showPage(\'{cap_l}\')">\n'
        f'      <div class="lb-rank rank-{rank}">#{rank}</div>'
        f'<div class="lb-stripe" style="background:{color}"></div>\n'
        f'      <div class="lb-name-block"><div class="lb-name">{captain}</div>'
        f'<div class="lb-record">{record}</div></div>\n'
        f'      <div class="lb-stats">\n'
        f'        <div class="lb-stat"><div class="lb-stat-label">Return</div>'
        f'<div class="lb-stat-value">{fmtd(s["ret"])}</div></div>\n'
        f'        <div class="lb-stat"><div class="lb-stat-label">Staked</div>'
        f'<div class="lb-stat-value">{fmtd(s["staked"])}</div></div>\n'
        f'        <div class="lb-stat"><div class="lb-stat-label">Net P&amp;L</div>'
        f'<div class="lb-stat-value {pnl_c}">{net_str}</div></div>\n'
        f'        <div class="lb-stat"><div class="lb-stat-label">Win %</div>'
        f'<div class="lb-stat-value">{s["wr"]}</div></div>\n'
        f'      </div><div class="lb-arrow">›</div>\n'
        f'    </div>\n'
    )


def rebuild_leaderboard_div(lb_section, all_stats, ranks, html_full):
    """Replace the <div class="leaderboard">…</div> block with updated cards."""
    ordered = sorted(CAPTAINS, key=lambda c: ranks[c])
    cards   = ''.join(
        build_lb_card(c, ranks[c], all_stats[c], outstanding_badge(c, html_full))
        for c in ordered
    )
    new_lb = f'  <div class="leaderboard">\n{cards}  </div>\n'
    return re.sub(
        r'  <div class="leaderboard">.*?  </div>\n',
        new_lb,
        lb_section,
        flags=re.DOTALL
    )


# ─────────────────────────────────────────────────────────────────────────────
# Stats bar
# ─────────────────────────────────────────────────────────────────────────────

def rebuild_stats_bar(lb_section, overall):
    new_bar = (
        f'  <div class="stats-bar">\n'
        f'    <div class="stat-item"><div class="stat-label">Total Bets</div>'
        f'<div class="stat-value">{overall["n"]}</div></div>\n'
        f'    <div class="stat-item"><div class="stat-label">Wins</div>'
        f'<div class="stat-value">{overall["wins"]}</div></div>\n'
        f'    <div class="stat-item"><div class="stat-label">Losses</div>'
        f'<div class="stat-value">{overall["losses"]}</div></div>\n'
        f'    <div class="stat-item"><div class="stat-label">Win Rate</div>'
        f'<div class="stat-value">{overall["wr"]}</div></div>\n'
        f'    <div class="stat-item"><div class="stat-label">Total Staked</div>'
        f'<div class="stat-value">${overall["staked"]:,.0f}</div></div>\n'
        f'    <div class="stat-item"><div class="stat-label">Total Return</div>'
        f'<div class="stat-value">{fmtd(overall["ret"])}</div></div>\n'
        f'    <div class="stat-item"><div class="stat-label">Net P&amp;L</div>'
        f'<div class="stat-value {pc(overall["net"])}">'
        f'{fmtd(overall["net"], signed=True)}</div></div>\n'
        f'  </div>\n'
    )
    return re.sub(
        r'  <div class="stats-bar">.*?  </div>\n',
        new_bar,
        lb_section,
        flags=re.DOTALL
    )


# ─────────────────────────────────────────────────────────────────────────────
# Account page — Bet Returns section
# ─────────────────────────────────────────────────────────────────────────────

def update_account_returns(acct_section, all_stats):
    """Update the Bet Returns table and mobile cards in the account section."""
    overall = {
        'staked': sum(all_stats[c]['staked'] for c in CAPTAINS),
        'ret':    sum(all_stats[c]['ret']    for c in CAPTAINS),
        'wins':   sum(all_stats[c]['wins']   for c in CAPTAINS),
        'losses': sum(all_stats[c]['losses'] for c in CAPTAINS),
        'n':      sum(all_stats[c]['n']      for c in CAPTAINS),
    }
    overall['net'] = overall['ret'] - overall['staked']
    overall['wr']  = wr_pct(overall['wins'], overall['n'])

    # --- Mobile cards ---
    # Ordered by net P&L descending for the mobile display
    mob_order = sorted(CAPTAINS, key=lambda c: -all_stats[c]['net'])
    mob_rows = ''
    for cap in mob_order:
        s   = all_stats[cap]
        col = 'var(--green)' if s['net'] >= 0 else 'var(--red)'
        mob_rows += (
            f'    <div class="mob-member-row">'
            f'<div><div class="mob-member-name">{cap}</div>'
            f'<div class="mob-member-sub">{s["n"]} bets · {s["wins"]}W {s["losses"]}L · {s["wr"]}</div></div>'
            f'<div class="mob-member-right">'
            f'<div class="mob-member-val" style="color:{col}">{fmtd(s["net"], signed=True)}</div>'
            f'<div class="mob-member-sub">{fmtd(s["ret"])} returned</div>'
            f'</div></div>\n'
        )
    # Totals mob row
    tot_col  = '#4ADE80' if overall['net'] >= 0 else '#F87171'
    mob_total = (
        f'    <div class="mob-totals-row">'
        f'<span class="mob-totals-label">'
        f'{overall["n"]} bets · {overall["wins"]}W {overall["losses"]}L · {overall["wr"]}'
        f'</span><span class="mob-totals-val" style="color:{tot_col}">'
        f'{fmtd(overall["net"], signed=True)}</span></div>\n'
    )

    acct_section = re.sub(
        r'  <div class="mob-returns-cards">.*?  </div>\n',
        f'  <div class="mob-returns-cards">\n{mob_rows}{mob_total}  </div>\n',
        acct_section, flags=re.DOTALL
    )

    # --- Desktop table rows (per captain, then total) ---
    # Build each captain row
    cap_rows = ''
    for cap in CAPTAINS:
        s    = all_stats[cap]
        col  = 'var(--green)' if s['net'] >= 0 else 'var(--red)'
        cap_rows += (
            f'        <tr style="border-bottom:1px solid var(--grey-line)">'
            f'<td style="padding:14px 20px;font-weight:700">{cap}</td>'
            f'<td style="padding:14px 20px;text-align:center">{s["n"]}</td>'
            f'<td style="padding:14px 20px;text-align:center">{s["wins"]}W &nbsp;{s["losses"]}L</td>'
            f'<td style="padding:14px 20px;text-align:center">{s["wr"]}</td>'
            f'<td style="padding:14px 20px;text-align:center;font-family:monospace">{fmtd(s["ret"])}</td>'
            f'<td style="padding:14px 20px;text-align:center;font-family:monospace;font-weight:700;color:{col}">'
            f'{fmtd(s["net"], signed=True)}</td></tr>\n'
        )
    # Total row
    tot_col2 = 'var(--green)' if overall['net'] >= 0 else 'var(--red)'
    total_row = (
        f'        <tr style="background:#F8F9FA;border-top:2px solid var(--navy)">'
        f'<td style="padding:14px 20px;font-weight:700;font-size:13px;text-transform:uppercase;letter-spacing:1px">Total</td>'
        f'<td style="padding:14px 20px;text-align:center;font-weight:700">{overall["n"]}</td>'
        f'<td style="padding:14px 20px;text-align:center;font-weight:700">{overall["wins"]}W &nbsp;{overall["losses"]}L</td>'
        f'<td style="padding:14px 20px;text-align:center;font-weight:700">{overall["wr"]}</td>'
        f'<td style="padding:14px 20px;text-align:center;font-family:monospace;font-weight:700">{fmtd(overall["ret"])}</td>'
        f'<td style="padding:14px 20px;text-align:center;font-family:monospace;font-weight:700;color:{tot_col2}">'
        f'{fmtd(overall["net"], signed=True)}</td></tr>\n'
    )

    # Replace tbody of the Bet Returns table
    acct_section = re.sub(
        r'      <tbody>\n        <tr.*?</tr>\n        <tr style="background:#F8F9FA.*?</tr>\n      </tbody>\n    </table>\n  </div></div>\n\n  <footer>',
        f'      <tbody>\n{cap_rows}{total_row}      </tbody>\n    </table>\n  </div></div>\n\n  <footer>',
        acct_section, flags=re.DOTALL
    )

    # Update "Total Bet Returns (2026)" figure in the account hero
    # This equals the total returns added to the pool from all bets
    # = net P&L from betting (return - staked)
    net_sign_val = '+' if overall['net'] >= 0 else ''
    acct_section = re.sub(
        r'(Total Bet Returns \(2026\)</div><div style="font-size:20px;font-weight:700;color:#4ADE80">)[^<]+',
        lambda m: m.group(1) + f'{fmtd(overall["net"], signed=True)}',
        acct_section
    )

    return acct_section, overall


# ─────────────────────────────────────────────────────────────────────────────
# Pool balance update
# ─────────────────────────────────────────────────────────────────────────────

def parse_pool_balance(html):
    """Extract the current pool balance from the HTML."""
    m = re.search(r'<div class="acct-bal"[^>]*>\$([0-9,]+\.[0-9]+)</div>', html)
    if m:
        return float(m.group(1).replace(',', ''))
    return None


def update_pool_balance(html, new_balance, date_str):
    """Update pool balance and AS AT date in both home and account sections."""
    # $X,XXX.XX pattern for the balance display
    bal_str  = f'${new_balance:,.2f}'
    date_str = date_str.upper()  # 'AS AT 30 JUN 2026'

    # Replace balance amounts
    html = re.sub(
        r'(<div class="acct-bal"[^>]*>)\$[0-9,]+\.[0-9]+</div>',
        lambda m: f'{m.group(1)}{bal_str}</div>',
        html
    )
    # Replace AS AT dates
    html = re.sub(
        r'AS AT \d+ [A-Z]+ \d{4}',
        f'AS AT {date_str}',
        html
    )
    # Footer "Account balance as at..."
    html = re.sub(
        r'Account balance as at \d+ [A-Za-z]+ \d{4}',
        f'Account balance as at {date_str.title()}',
        html
    )
    return html


# ─────────────────────────────────────────────────────────────────────────────
# Home page mob-totals-row (bet returns)
# ─────────────────────────────────────────────────────────────────────────────

def update_home_mob_totals(home_section, overall):
    tot_col = '#4ADE80' if overall['net'] >= 0 else '#F87171'
    new_row = (
        f'    <div class="mob-totals-row">'
        f'<span class="mob-totals-label">'
        f'{overall["n"]} bets · {overall["wins"]}W {overall["losses"]}L · {overall["wr"]}'
        f'</span><span class="mob-totals-val" style="color:{tot_col}">'
        f'{fmtd(overall["net"], signed=True)}</span></div>'
    )
    return re.sub(
        r'    <div class="mob-totals-row"><span class="mob-totals-label">\d+ bets.*?</span></div>',
        new_row,
        home_section,
        flags=re.DOTALL
    )


# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULE — mark bets as logged
# ─────────────────────────────────────────────────────────────────────────────

def mark_schedule_logged(html, captain, date_str):
    """Set logged: false → logged: true for a specific captain/date entry."""
    pattern = (
        rf"(\{{ date: '{re.escape(date_str)}', captain: '{re.escape(captain)}',"
        rf"\s+)logged: false"
    )
    return re.sub(pattern, lambda m: m.group(1) + 'logged: true', html)


# ─────────────────────────────────────────────────────────────────────────────
# Header "Updated" date
# ─────────────────────────────────────────────────────────────────────────────

def update_header_date(html, date_str):
    return re.sub(
        r'Updated \d+ [A-Za-z]+ \d{4}',
        f'Updated {date_str}',
        html
    )


# ─────────────────────────────────────────────────────────────────────────────
# Section splitter
# ─────────────────────────────────────────────────────────────────────────────

SECTION_RE = re.compile(r'(<!-- ═══════════════ [A-Z ]+-->)')

def split_html(html):
    """Split on section comments. Returns [(marker, content), ...]"""
    parts  = SECTION_RE.split(html)
    result = [('', parts[0])]
    for i in range(1, len(parts), 2):
        marker  = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ''
        result.append((marker, content))
    return result

def join_html(sections):
    return ''.join(m + c for m, c in sections)

def find_section(sections, name):
    """Return index of section whose marker contains `name`."""
    for i, (m, _) in enumerate(sections):
        if name.upper() in m.upper():
            return i
    return -1


# ─────────────────────────────────────────────────────────────────────────────
# Excel spreadsheet updater
# ─────────────────────────────────────────────────────────────────────────────

def add_bet_to_xlsx(bet, savings=SAVINGS_WEEKLY):
    """Append a new bet row to PIC_2026_Tracker.xlsx."""
    if not HAS_OPENPYXL:
        print("  Skipping spreadsheet update (openpyxl not available).")
        return

    if not XLSX_F.exists():
        print(f"  ⚠  Spreadsheet not found: {XLSX_F}")
        return

    wb  = openpyxl.load_workbook(XLSX_F)
    ws  = wb.active  # first sheet

    # Find last row with data in column A (Date)
    last_row = 1
    for row in ws.iter_rows(min_col=1, max_col=1, values_only=False):
        cell = row[0]
        if cell.value is not None:
            last_row = cell.row

    new_row = last_row + 1
    prev    = last_row

    # Columns: A=Date, B=Captain, C=Savings, D=Description, E=Odds,
    #          F=Stake, G=Return, H=Win/Loss, I=Pool Balance, J=Notes
    ws.cell(new_row, 1).value = bet['date']
    ws.cell(new_row, 2).value = bet['captain']
    ws.cell(new_row, 3).value = savings

    # Bet description
    ws.cell(new_row, 4).value = bet.get('desc', '')

    # Odds
    odds = bet.get('odds', '')
    try:
        ws.cell(new_row, 5).value = float(odds) if odds and odds not in ('—', '-', '') else ''
    except (ValueError, TypeError):
        ws.cell(new_row, 5).value = odds

    # Stake
    ws.cell(new_row, 6).value = float(bet.get('stake', 30))

    # Return
    ret_val = float(bet.get('return', 0))
    ws.cell(new_row, 7).value = ret_val

    # Win/Loss
    ws.cell(new_row, 8).value = bet.get('result', '')

    # Pool Balance formula  =IF(G{n}="",I{n-1}+C{n},I{n-1}+C{n}+G{n})
    ws.cell(new_row, 9).value = (
        f'=IF(G{new_row}="",I{prev}+C{new_row},I{prev}+C{new_row}+G{new_row})'
    )

    # Notes
    ws.cell(new_row, 10).value = bet.get('notes', '')

    wb.save(XLSX_F)
    print(f"  ✓  Spreadsheet row {new_row} added.")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print()
    print('  PIC — Processing bet log...')
    print()

    # 1. Read log
    if not LOG_F.exists():
        print('  No bets_log.json found. Nothing to do.')
        return

    with open(LOG_F, encoding='utf-8') as f:
        log = json.load(f)

    bets = log.get('bets', [])
    if not bets:
        print('  bets_log.json is empty. Nothing to do.')
        return

    settled = [b for b in bets if b.get('result') in ('Win', 'Loss')]
    if not settled:
        print(f'  {len(bets)} pending bet(s) in log — no settled bets to process.')
        return

    print(f'  Found {len(settled)} settled bet(s) to process.')

    # 2. Read HTML
    if not HTML_F.exists():
        print(f'  ✗  Dashboard not found: {HTML_F}')
        sys.exit(1)

    html = HTML_F.read_text(encoding='utf-8')
    sections = split_html(html)

    # 3. Group new bets by captain
    by_captain = {c: [] for c in CAPTAINS}
    for b in settled:
        cap = b.get('captain', '')
        if cap in by_captain:
            by_captain[cap].append(b)
        else:
            print(f'  ⚠  Unknown captain: {cap}  — skipping.')

    # 4. Update each captain's section
    all_stats = {}
    for captain in CAPTAINS:
        idx = find_section(sections, captain.upper())
        if idx < 0:
            print(f'  ⚠  Section not found for {captain}')
            continue
        sec, s = update_captain_section(sections[idx][1], by_captain[captain])
        sections[idx] = (sections[idx][0], sec)
        all_stats[captain] = s
        if by_captain[captain]:
            print(f'  ✓  {captain}: {len(by_captain[captain])} bet(s) added.')

    # 5. Re-rank and update rank numbers in captain sections
    ranks = rank_captains(all_stats)
    for captain in CAPTAINS:
        idx = find_section(sections, captain.upper())
        if idx >= 0:
            sec = update_bettor_rank(sections[idx][1], ranks[captain])
            sections[idx] = (sections[idx][0], sec)

    # 6. Rebuild leaderboard (needs full html for SCHEDULE outstanding check)
    html_tmp   = join_html(sections)  # temp join for SCHEDULE context
    lb_idx     = find_section(sections, 'LEADERBOARD')
    if lb_idx >= 0:
        lb_sec = rebuild_leaderboard_div(sections[lb_idx][1], all_stats, ranks, html_tmp)
        # Overall stats
        overall = {
            'staked': sum(all_stats[c]['staked'] for c in CAPTAINS),
            'ret':    sum(all_stats[c]['ret']    for c in CAPTAINS),
            'wins':   sum(all_stats[c]['wins']   for c in CAPTAINS),
            'losses': sum(all_stats[c]['losses'] for c in CAPTAINS),
            'n':      sum(all_stats[c]['n']      for c in CAPTAINS),
        }
        overall['net'] = overall['ret'] - overall['staked']
        overall['wr']  = wr_pct(overall['wins'], overall['n'])
        lb_sec = rebuild_stats_bar(lb_sec, overall)
        sections[lb_idx] = (sections[lb_idx][0], lb_sec)

    # 7. Update account page
    acct_idx = find_section(sections, 'ACCOUNT')
    if acct_idx >= 0:
        acct_sec, overall = update_account_returns(sections[acct_idx][1], all_stats)
        sections[acct_idx] = (sections[acct_idx][0], acct_sec)

    # 8. Update home page mob totals row
    home_idx = find_section(sections, 'HOME')
    if home_idx >= 0:
        home_sec = update_home_mob_totals(sections[home_idx][1], overall)
        sections[home_idx] = (sections[home_idx][0], home_sec)

    # 9. Rejoin HTML
    html = join_html(sections)

    # 10. Pool balance update
    cur_bal = parse_pool_balance(html)
    if cur_bal is not None:
        new_bal = cur_bal
        for b in settled:
            new_bal += SAVINGS_WEEKLY + float(b.get('return', 0))
        bal_date = today_str()
        html = update_pool_balance(html, new_bal, bal_date)
        print(f'  ✓  Pool balance: ${cur_bal:,.2f} → ${new_bal:,.2f}')

    # 11. Mark SCHEDULE entries as logged
    for b in settled:
        html = mark_schedule_logged(html, b['captain'], b['date'])
        print(f'  ✓  SCHEDULE: {b["captain"]} {b["date"]} marked logged.')

    # 12. Update header date
    html = update_header_date(html, today_str())

    # 13. Write HTML
    HTML_F.write_text(html, encoding='utf-8')
    print(f'  ✓  Dashboard saved.')

    # 14. Update spreadsheet
    for b in settled:
        add_bet_to_xlsx(b)

    # 15. Clear log
    LOG_F.write_text('{"bets": []}\n', encoding='utf-8')
    print(f'  ✓  bets_log.json cleared.')
    print()
    print('  Done! Run push.bat to publish.')
    print()


if __name__ == '__main__':
    main()
