"""그린바이오 강의자료 빌드 — 사용법: python build.py specs/07-2.json [specs/07-3.json ...]
spec(JSON) 하나 = 차시 하나. PPT(노트에 대본 내장) + 미니맥스 대본 docx를 output/에 만들고 QA 결과를 출력한다.
QA 기준을 못 넘으면 종료코드 1 (대본 숫자 0개 / 25분 이상 / 끊긴참조 0 / 이전 텍스트 잔여 없음 / 슬롯 누락 없음)."""
import sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
import engine as E

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "template.pptx"
OUT = ROOT / "output"
MIN_MINUTES = 25.0

def run(spec_path):
    s = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    w, c = s["week"], s["cha"]
    OUT.mkdir(exist_ok=True)
    stem = f"{w}주차_{c}차시_{s['file_title']}"
    pptx = OUT / f"{stem}.pptx"
    docx = OUT / f"{w}주차_{c}차시_미니맥스대본.docx"
    miss = E.build(str(TEMPLATE), str(pptx), w, c, s["content"], s["notes"])
    rep = E.qa(str(pptx), old_words=tuple(s.get("old_words", ["WEEK 5"])))
    E.script_docx(str(docx), "그린바이오 전자상거래개론 · 2026학년도 2학기",
                  f"{w}주차 {c}차시 · {s['topic']}", s["slide_titles"], s["notes"])
    expected = {f"S{si}.{n}" for si, sl in E.SLOTS.items() for n in sl}
    empty = sorted(expected - set(s["content"]))
    ok = (not miss and rep["대본 속 아라비아 숫자"] == "없음" and rep["예상 분량(분)"] >= MIN_MINUTES
          and rep["끊긴참조/자동재생 잔여"] == 0 and rep["이전 텍스트 잔여"] == "없음")
    print(f"\n=== {stem} ===")
    print("PPT :", pptx.relative_to(ROOT)); print("대본:", docx.relative_to(ROOT))
    for k, v in rep.items(): print(f"  {k}: {v}")
    if miss: print("  ⚠ 매핑 실패 슬롯:", miss)
    if empty: print("  ⚠ spec에 없는 슬롯(템플릿 원문이 남음):", empty)
    print("  결과:", "✅ 통과" if ok and not empty else "❌ 기준 미달")
    return ok and not empty

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    results = [run(p) for p in sys.argv[1:]]
    sys.exit(0 if all(results) else 1)
