from pathlib import Path
import json, re, sys, time
from urllib.request import Request, urlopen
from html import unescape

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
PT_EXTRAS = ROOT / "pt" / "extras"

BOOKS = [
    {
        "id": "JUB",
        "book": "Livro dos Jubileus",
        "chapters": 50,
        "url": "https://escriturasperdidas.com.br/pt/jubileus/{chapter}",
    },
    {
        "id": "1EN",
        "book": "1 Enoque",
        "chapters": 108,
        "url": "https://escriturasperdidas.com.br/pt/1-enoque/{chapter}",
    },
]

MOJIBAKE = ("Ã", "Â", "â€", "â€™", "â€œ", "â€", "�")

def html_to_text(fragment: str) -> str:
    fragment = re.sub(r"<script\b[^>]*>.*?</script>", "", fragment, flags=re.I | re.S)
    fragment = re.sub(r"<style\b[^>]*>.*?</style>", "", fragment, flags=re.I | re.S)
    fragment = re.sub(r"<br\s*/?>", " ", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    fragment = unescape(fragment)
    fragment = re.sub(r"\s+", " ", fragment).strip()
    return fragment

def download_utf8(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 SemearBiblia/1.0",
            "Accept-Language": "pt-BR,pt;q=0.9",
        },
    )
    with urlopen(req, timeout=45) as r:
        raw = r.read()

    # Força a interpretação correta dos bytes da página.
    return raw.decode("utf-8", errors="strict")

def extract_verses(page_html: str):
    verses = []

    # A página usa parágrafos para cada versículo.
    for m in re.finditer(r"<p\b[^>]*>(.*?)</p>", page_html, flags=re.I | re.S):
        txt = html_to_text(m.group(1))
        vm = re.match(r"^\s*(\d{1,3})\s*(.+)$", txt, flags=re.S)
        if vm:
            verses.append({
                "verse": int(vm.group(1)),
                "text": vm.group(2).strip(),
            })

    # Remove duplicados mantendo o primeiro e ordena.
    unique = {}
    for v in verses:
        unique.setdefault(v["verse"], v["text"])

    return [{"verse": n, "text": unique[n]} for n in sorted(unique)]

def has_mojibake(text: str) -> bool:
    return any(x in text for x in MOJIBAKE)

def save_chapter(book, chapter):
    url = book["url"].format(chapter=chapter)
    page = download_utf8(url)
    verses = extract_verses(page)

    if not verses:
        raise RuntimeError(f"Nenhum versículo encontrado: {url}")

    payload = {
        "book_id": book["id"],
        "book": book["book"],
        "chapter": chapter,
        "language": "pt-BR",
        "collection": "extras",
        "source": "Escrituras Perdidas",
        "source_url": url,
        "verses": verses,
    }

    serialized = json.dumps(payload, ensure_ascii=False, indent=2)

    if has_mojibake(serialized):
        found = [x for x in MOJIBAKE if x in serialized]
        raise RuntimeError(
            f"Texto ainda contém possível codificação quebrada em {url}: {found}"
        )

    out_dir = PT_EXTRAS / book["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{chapter}.json"
    out_file.write_text(serialized, encoding="utf-8")
    return len(verses)

def main():
    if not (ROOT / "pt").exists():
        raise SystemExit(f"Pasta 'pt' não encontrada em: {ROOT}")

    print("SEMEAR BIBLIA - REGERAR TEXTOS PT EM UTF-8")
    print("Raiz:", ROOT)
    print()

    totals = {}
    for book in BOOKS:
        total = 0
        print(f"== {book['book']} ==")
        for ch in range(1, book["chapters"] + 1):
            count = save_chapter(book, ch)
            total += count
            print(f"{book['id']} {ch}/{book['chapters']} - {count} versículos")
            time.sleep(0.10)
        totals[book["id"]] = total
        print()

    # Validação final de todos os JSONs gerados.
    checked = 0
    for book in BOOKS:
        folder = PT_EXTRAS / book["id"]
        files = sorted(folder.glob("*.json"), key=lambda p: int(p.stem))
        if len(files) != book["chapters"]:
            raise RuntimeError(
                f"{book['id']}: esperado {book['chapters']} capítulos, encontrado {len(files)}."
            )

        for fp in files:
            data = json.loads(fp.read_text(encoding="utf-8"))
            raw = json.dumps(data, ensure_ascii=False)
            if has_mojibake(raw):
                raise RuntimeError(f"Possível mojibake ainda presente: {fp}")
            checked += 1

    print("==============================================")
    print("CONCLUIDO")
    print("==============================================")
    print(f"Jubileus: {totals['JUB']} versículos")
    print(f"1 Enoque: {totals['1EN']} versículos")
    print(f"Arquivos validados: {checked}")
    print("Codificação: UTF-8")
    print("Nenhum marcador comum de mojibake encontrado.")

if __name__ == "__main__":
    main()
