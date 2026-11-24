# 🌅 08:40 아침 브리핑 — 5블록 대시보드 채우는 법

`https://kebira.github.io/diary/brief/` 의 **08:40 개장 전 브리핑**은 아래 **5개 블록만** 보여준다.
다른 시간대(16:00 장 마감 · 19:30 해외선물)는 기존 형식 그대로이며 이 문서와 무관하다.

| | 블록 | 데이터 위치 | 표시 |
|---|---|---|---|
| ① | 전일 나스닥 | `morning.nasdaq` | 전종 `prev.close` · 전고 `prev.high` · 전저 `prev.low` · 당일 시가 `today.open`, 그리고 **`시가 − 전일종` 계산 행** |
| ② | 코스피200 선물 | `morning.night` | 전일 정규장 종가 `prevSessionClose` · 야간선물 종가 `nightClose` · 당일 예상 시가 `expOpen`, 그리고 **`예상 − 전일종` · `예상 − 야간종` 계산 행 2개** |
| ③ | 당일 장 재료 | `morning.marketNews` | 3~5건 (`tag`, `t`, `d`) |
| ④ | 시사 핫뉴스 | `morning.hotNews` | 3~5건 (`tag`, `t`, `d`) |
| ⑤ | 날씨 + 일정 | `morning.weather`, `morning.schedule` | 기온·체감·최고/최저·강수·미세먼지, Google 캘린더 오늘 일정 |

차이(포인트·%)는 화면과 메일에서 **자동 계산**된다. 숫자만 정확히 넣으면 된다.

## 08:40 채우기 순서(발송 직전 조회)

1. **`brief/morning.json` 만 고친다.** `index.html` 은 손대지 않는다(같은 값이 안전판으로 들어 있을 뿐이고,
   페이지는 열릴 때 `morning.json` 을 읽어 맨 앞 세션을 덮어쓴다).
2. `morning.json` 구조:

```json
{
  "updated_at": "2026-11-25T08:30:00+09:00",
  "session": {
    "id": "2026-11-25-0840",
    "date": "2026-11-25",
    "weekday": "수",
    "time": "08:40",
    "kind": "개장 전",
    "mode": "morning",
    "status": "live",
    "sub": "한 줄 요약",
    "live": "개장 전",
    "next": "16:00 장 마감 종합 & 내일장 시나리오",
    "morning": {
      "asOf": "2026-11-25 08:30",
      "notice": null,
      "nasdaq": {
        "name": "나스닥100 선물", "tag": "NQ",
        "prevDate": "11/24 미장 · 06:00 마감",
        "prev": { "close": 26812.75, "high": 27137.00, "low": 25426.75 },
        "today": { "open": 26888.00, "label": "당일 시가 (08:00 시초)" },
        "pendingNote": null
      },
      "night": {
        "name": "코스피200 선물", "code": "2612",
        "prevSessionClose": 778.10, "prevSessionMeta": "11/24 정규장 종가",
        "nightClose": 756.95,       "nightCloseMeta": "06:00 야간 종가",
        "expOpen": 760.00,          "expOpenMeta": "08:35 동시호가 예상",
        "pendingNote": null
      },
      "marketNews": [ { "tag": "미국", "t": "제목", "d": "설명" } ],
      "hotNews":    [ { "tag": "정치", "t": "제목", "d": "설명" } ],
      "weather": {
        "place": "구로구 개봉동", "asOf": "11/25 04:35", "cond": "구름 조금",
        "now": "-2", "feels": "-1", "high": "8", "low": "-3", "rain": "0%",
        "airGrade": "좋음", "pm10": "20", "pm25": "7", "station": "구로구 측정소 1.9km"
      },
      "schedule": [ { "time": "14:00", "title": "EL치과 진료 예약", "note": "당산" } ],
      "scheduleNote": null
    }
  }
}
```

   - `status`: 채우기 전 `pending`(상단에 "준비 중" 안내), 채운 뒤 `live`.
   - `id`: `YYYY-MM-DD-0840` (그날 날짜). 같은 id면 맨 앞 세션을 교체한다.
   - ①·② 칸이 `null` 이면 화면에 `—` 로 나온다. **없는 값을 추정해 넣지 않는다.**
   - ⑤ `schedule` 이 비면 `scheduleNote` 문구를 보여준다. 일정 제목만 넣고 주소는 넣지 않는다(공개 페이지).
   - 날씨는 `weather '37.4998, 126.8678'` (개봉동 기준), 일정은
     `gog --readonly calendar events --today --all --results-only`.
3. 점검: `python3 brief/build_morning.py` — 오류(exit 1)가 없어야 배포한다.
4. 메일 본문: `python3 brief/build_morning.py --mail` →
   `brief/out/morning-mail.html`, `brief/out/morning-mail.txt` 생성 후

```
gog gmail drafts create --to han63soo@gmail.com \
  --subject "🌅 11/25 (수) 08:40 아침 브리핑" \
  --body-file kebira-diary/brief/out/morning-mail.txt \
  --body-html-file kebira-diary/brief/out/morning-mail.html
gog gmail drafts get <draftId> && gog gmail drafts send <draftId>
```

5. 배포: `kebira-diary` 에서 `git add brief && git commit && git push origin main`.
   GitHub Pages(legacy, main)가 1~2분 안에 반영한다.
6. 확인: `curl -s -o /dev/null -w "%{http_code}" https://kebira.github.io/diary/brief/morning.json`
   및 페이지를 열어 ①~⑤가 다 찼는지 본다.

## 참고

- 차이 계산식은 화면(`mDiffRow`)과 메일(`diffbar`) 모두 `a − b` 포인트, `(a−b)/b×100` %.
  상승 빨강(`--up`/`#dc2626`), 하락 파랑(`--dn`/`#2563eb`).
- 코스피200 현물 지수·코스닥은 넣지 않는다(한연수 님 지정). 아침 브리핑의 선물은 **2612(12월물)** 기준.
- `brief/out/` 은 배포물이 아니다(`.gitignore` 에 포함).
