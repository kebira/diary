#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
08:40 아침 브리핑 5블록 — 점검 + 메일 본문 생성기
================================================================
사용법
  python3 brief/build_morning.py                 # morning.json 점검만
  python3 brief/build_morning.py --mail          # 점검 + 메일 본문(out/) 생성
  python3 brief/build_morning.py --file 경로.json

점검(exit 1) 항목 — 08:30 채움 뒤 반드시 통과해야 하는 것
  · session.id/date/weekday/time(=08:40)/mode=morning
  · status=live 이면
      ① 전종·전고·전저·당일 시가 숫자
      ② 전일 정규장 종가·야간선물 종가·당일 예상 시가 숫자
  · ③ marketNews 3~5건, ④ hotNews 3~5건, 각 항목 tag/t 필수
  · ⑤ weather.place, schedule 은 배열

메일 본문은 brief/out/morning-mail.html / .txt 로 저장된다.
  gog gmail drafts create --to ... --subject '...' \
      --body-file brief/out/morning-mail.txt \
      --body-html-file brief/out/morning-mail.html
"""
import argparse
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def load(path: pathlib.Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def fmt(v, dec=2):
    return f"{v:,.{dec}f}" if num(v) else "—"


def diff_of(a, b):
    """a - b 를 포인트·%로."""
    if not (num(a) and num(b)) or b == 0:
        return None, None
    d = round(a - b, 2)
    return d, round(d / b * 100, 2)


def diff_text(d, r):
    if d is None:
        return "08:40 확인"
    return f"{d:+,.2f}p ({r:+.2f}%)"


def check(doc):
    errs, warns = [], []
    s = doc.get("session") or {}
    m = s.get("morning") or {}
    if not s.get("id"):
        errs.append("session.id 없음")
    if s.get("mode") != "morning":
        errs.append('session.mode 가 "morning" 이 아님')
    for k in ("date", "weekday", "time", "kind"):
        if not s.get(k):
            errs.append(f"session.{k} 없음")
    if s.get("time") and s.get("time") != "08:40":
        warns.append(f"session.time 이 {s.get('time')} — 아침 브리핑은 08:40")

    nq = m.get("nasdaq") or {}
    prev, today = nq.get("prev") or {}, nq.get("today") or {}
    nt = m.get("night") or {}
    live = s.get("status") in ("live", "done")
    for key, label in (("close", "①전종"), ("high", "①전고"), ("low", "①전저")):
        if not num(prev.get(key)):
            (errs if live else warns).append(f"{label} 값 없음")
    if not num(today.get("open")):
        (errs if live else warns).append("①당일 시가 값 없음")
    for key, label in (("prevSessionClose", "②전일 정규장 종가"),
                       ("nightClose", "②야간선물 종가"),
                       ("expOpen", "②당일 예상 시가")):
        if not num(nt.get(key)):
            (errs if live else warns).append(f"{label} 값 없음")

    for key, name, lo, hi in (("marketNews", "③장 뉴스", 3, 5), ("hotNews", "④시사", 3, 5)):
        items = m.get(key) or []
        if not (lo <= len(items) <= hi):
            (errs if live else warns).append(f"{name} {len(items)}건 — {lo}~{hi}건이어야 함")
        for i, it in enumerate(items, 1):
            if not it.get("tag") or not it.get("t"):
                errs.append(f"{name} {i}번째에 tag/t 없음")

    w = m.get("weather") or {}
    if not w.get("place"):
        warns.append("⑤weather.place 없음")
    if not isinstance(m.get("schedule"), list):
        errs.append("⑤schedule 이 배열이 아님")
    if s.get("status") == "pending":
        warns.append("status=pending — 08:40 채움 전 상태")
    return errs, warns


def mail_html(s):
    m = s.get("morning") or {}
    nq = m.get("nasdaq") or {}
    prev, today = nq.get("prev") or {}, nq.get("today") or {}
    nt = m.get("night") or {}
    w = m.get("weather") or {}
    e = html.escape

    def cell(v, label, sub, color="#0f172a", width="33%"):
        return (
            f'<td width="{width}" style="padding:4px;vertical-align:top">'
            f'<div style="background:#f1f5f9;border:1px solid #e2e8f0;border-radius:10px;padding:8px 9px">'
            f'<div style="font-size:10px;color:#64748b;font-weight:700;line-height:1.3">{e(label)}</div>'
            f'<div style="font-size:17px;font-weight:800;color:{color};letter-spacing:-.5px;margin-top:2px">{e(v)}</div>'
            f'<div style="font-size:9.5px;color:#94a3b8;margin-top:2px;line-height:1.3">{e(sub)}</div></div></td>'
        )

    def diffbar(label, a, b):
        d, r = diff_of(a, b)
        color = "#dc2626" if (d or 0) > 0 else "#2563eb" if (d or 0) < 0 else "#64748b"
        return (
            f'<div style="margin-top:5px;padding:7px 11px;border:1px solid #e2e8f0;background:#fafbfc;border-radius:9px">'
            f'<span style="font-size:10.5px;color:#64748b;font-weight:700">{e(label)}</span> '
            f'<b style="font-size:15px;color:{color};letter-spacing:-.4px;margin-left:6px">{e(diff_text(d, r))}</b></div>'
        )

    def news_rows(items):
        return "".join(
            f'<tr><td style="padding:7px 0;border-bottom:1px solid #eef2f7;vertical-align:top">'
            f'<span style="display:inline-block;font-size:10px;font-weight:700;color:#475569;background:#eef2f7;border-radius:4px;padding:1px 5px;margin-right:5px">{e(n.get("tag",""))}</span>'
            f'<b style="font-size:13px;color:#0f172a">{e(n.get("t",""))}</b>'
            f'<div style="font-size:11.5px;color:#475569;line-height:1.5;margin-top:2px">{e(n.get("d",""))}</div>'
            f'</td></tr>'
            for n in items
        )

    sched = m.get("schedule") or []
    sched_html = "".join(
        f'<div style="font-size:12.5px;color:#0f172a;padding:4px 0"><b style="color:#2563eb">{e(x.get("time",""))}</b> '
        f'{e(x.get("title",""))}'
        + (f'<span style="color:#94a3b8;font-size:10px"> {e(x.get("note",""))}</span>' if x.get("note") else "")
        + "</div>"
        for x in sched
    ) or f'<div style="font-size:12px;color:#64748b">{e(m.get("scheduleNote") or "오늘 등록된 일정이 없습니다.")}</div>'

    def head(no, title, meta=""):
        return (
            f'<div style="margin:18px 0 6px;padding-bottom:5px;border-bottom:2px solid #e2e8f0">'
            f'<span style="display:inline-block;width:18px;height:18px;line-height:18px;text-align:center;border-radius:5px;background:#4f46e5;color:#fff;font-size:11px;font-weight:800">{no}</span> '
            f'<b style="font-size:13px;color:#0f172a">{e(title)}</b>'
            f'<span style="float:right;font-size:10px;color:#94a3b8;padding-top:2px">{e(meta)}</span></div>'
        )

    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;-webkit-text-size-adjust:100%">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:16px 10px">
<tr><td align="center">
<table role="presentation" width="480" cellpadding="0" cellspacing="0" style="max-width:480px;width:100%;background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden">
<tr><td style="background:#1e293b;padding:13px 16px">
  <div style="font-size:15px;font-weight:800;color:#ffffff;letter-spacing:-.3px">🌅 {e(s.get("date",""))} ({e(s.get("weekday",""))}) {e(s.get("time","08:40"))} 아침 브리핑</div>
  <div style="font-size:10.5px;color:#94a3b8;margin-top:3px">나스닥 · 코스피200 선물 · 장 뉴스 · 시사 · 날씨·일정 &nbsp;|&nbsp; {e(m.get("asOf",""))} 조회</div>
</td></tr>
<tr><td style="padding:4px 12px 6px">

{head("①", "전일 나스닥", nq.get("prevDate",""))}
<div style="font-size:11px;color:#64748b;font-weight:700;margin:2px 0 4px">{e(nq.get("name","나스닥100 선물"))}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
{cell(fmt(prev.get("close")), "전종", "전일 종가", width="25%")}{cell(fmt(prev.get("high")), "전고", "전일 고가", width="25%")}
{cell(fmt(prev.get("low")), "전저", "전일 저가", width="25%")}{cell(fmt(today.get("open")), "당일 시가", today.get("label") or "08:00 시초", "#1d4ed8", "25%")}
</tr></table>
{diffbar("당일 시가 − 전일 종가", today.get("open"), prev.get("close"))}

{head("②", "코스피200 선물 · 당일 예상가", nt.get("code",""))}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
{cell(fmt(nt.get("prevSessionClose")), "전일 정규장 종가", nt.get("prevSessionMeta") or "")}
{cell(fmt(nt.get("nightClose")), "야간선물 종가", nt.get("nightCloseMeta") or "")}
{cell(fmt(nt.get("expOpen")), "당일 예상 시가", nt.get("expOpenMeta") or "", "#1d4ed8")}
</tr></table>
{diffbar("당일 예상가 − 전일 종가", nt.get("expOpen"), nt.get("prevSessionClose"))}
{diffbar("당일 예상가 − 야간선물 종가", nt.get("expOpen"), nt.get("nightClose"))}

{head("③", "당일 장에 영향을 줄 뉴스")}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{news_rows(m.get("marketNews") or [])}</table>

{head("④", "시사 핫뉴스", "정치·사회·경제")}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{news_rows(m.get("hotNews") or [])}</table>

{head("⑤", "오늘 날씨 · 내 일정", w.get("asOf",""))}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
{cell(e((w.get("now") or "—") + "°"), "지금" + (" · " + e(w.get("place","")) if w.get("place") else ""), "체감 " + e((w.get("feels") or "—") + "° · " + (w.get("cond") or "")))}
{cell(e((w.get("high") or "—") + "° / " + (w.get("low") or "—") + "°"), "최고 / 최저", "강수 " + e(w.get("rain") or "—"))}
{cell(e(w.get("airGrade") or "—"), "미세먼지", ("PM10 " + e(w.get("pm10") or "-") + " · PM2.5 " + e(w.get("pm25") or "-")) if w.get("pm10") else "08:40 확인")}
</tr></table>
<div style="margin-top:10px;font-size:11px;font-weight:700;color:#64748b">오늘 일정 · Google 캘린더</div>
{sched_html}

<div style="margin-top:16px;padding-top:9px;border-top:1px solid #e2e8f0;font-size:9.5px;color:#94a3b8;line-height:1.6">
  수치는 {e(m.get("asOf",""))} 조회 기준입니다. 08:40 아침 브리핑은 ① 나스닥 4개 수치·차이 · ② 선물 3개 수치·차이 · ③ 장 뉴스 · ④ 시사 · ⑤ 날씨·일정만 담습니다.<br>
  대시보드: <a href="https://kebira.github.io/diary/brief/" style="color:#4f46e5">kebira.github.io/diary/brief</a> · 투자 판단의 최종 책임은 본인에게 있습니다.
</div>
</td></tr></table>
</td></tr></table></body></html>
"""


def mail_text(s):
    m = s.get("morning") or {}
    nq = m.get("nasdaq") or {}
    prev, today = nq.get("prev") or {}, nq.get("today") or {}
    nt = m.get("night") or {}
    w = m.get("weather") or {}
    L = []
    L.append(f"🌅 {s.get('date','')} ({s.get('weekday','')}) {s.get('time','08:40')} 아침 브리핑")
    L.append(f"{m.get('asOf','')} 조회 · kebira.github.io/diary/brief/")
    L.append("")
    L.append(f"① 전일 나스닥 — {nq.get('name','나스닥100 선물')} ({nq.get('prevDate','')})")
    L.append(f"   전종 {fmt(prev.get('close'))} · 전고 {fmt(prev.get('high'))} · 전저 {fmt(prev.get('low'))} · 당일 시가 {fmt(today.get('open'))}")
    L.append(f"   당일 시가 − 전일 종가 = {diff_text(*diff_of(today.get('open'), prev.get('close')))}")
    L.append("")
    L.append(f"② {nt.get('name','코스피200 선물')} · 당일 예상가")
    L.append(f"   전일 정규장 종가 {fmt(nt.get('prevSessionClose'))} · 야간선물 종가 {fmt(nt.get('nightClose'))} · 당일 예상 시가 {fmt(nt.get('expOpen'))}")
    L.append(f"   당일 예상가 − 전일 종가 = {diff_text(*diff_of(nt.get('expOpen'), nt.get('prevSessionClose')))}")
    L.append(f"   당일 예상가 − 야간선물 종가 = {diff_text(*diff_of(nt.get('expOpen'), nt.get('nightClose')))}")
    L.append("")
    L.append("③ 당일 장에 영향을 줄 뉴스")
    for i, n in enumerate(m.get("marketNews") or [], 1):
        L.append(f"   {i}. [{n.get('tag','')}] {n.get('t','')}")
        if n.get("d"):
            L.append(f"      {n['d']}")
    L.append("")
    L.append("④ 시사 핫뉴스")
    for i, n in enumerate(m.get("hotNews") or [], 1):
        L.append(f"   {i}. [{n.get('tag','')}] {n.get('t','')}")
        if n.get("d"):
            L.append(f"      {n['d']}")
    L.append("")
    L.append(f"⑤ 오늘 날씨 · 내 일정 — {w.get('place','')} {w.get('asOf','')}")
    L.append(f"   지금 {w.get('now','—')}° (체감 {w.get('feels','—')}°) · 최고 {w.get('high','—')}° / 최저 {w.get('low','—')}° · 강수 {w.get('rain','—')}")
    L.append(f"   미세먼지 {w.get('airGrade','—')} (PM10 {w.get('pm10','-')} · PM2.5 {w.get('pm25','-')})")
    sched = m.get("schedule") or []
    if sched:
        for x in sched:
            L.append(f"   {x.get('time','')} {x.get('title','')}" + (f" ({x['note']})" if x.get("note") else ""))
    else:
        L.append(f"   {m.get('scheduleNote') or '오늘 등록된 일정이 없습니다.'}")
    L.append("")
    L.append("투자 판단의 최종 책임은 본인에게 있습니다.")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=str(ROOT / "morning.json"))
    ap.add_argument("--mail", action="store_true", help="메일 본문(html/txt) 생성")
    a = ap.parse_args()

    path = pathlib.Path(a.file)
    doc = load(path)
    errs, warns = check(doc)
    print(f"점검: {path}")
    for w in warns:
        print(f"  · 경고 {w}")
    for e in errs:
        print(f"  ✗ 오류 {e}")
    if not errs:
        print("  ✓ 필수 항목 통과")
    if errs:
        return 1

    if a.mail:
        s = doc["session"]
        out = ROOT / "out"
        out.mkdir(exist_ok=True)
        (out / "morning-mail.html").write_text(mail_html(s), encoding="utf-8")
        (out / "morning-mail.txt").write_text(mail_text(s), encoding="utf-8")
        print(f"  → {out/'morning-mail.html'}")
        print(f"  → {out/'morning-mail.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
