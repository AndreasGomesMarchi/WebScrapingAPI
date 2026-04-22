"""
Web scraping de bolsas de estudo para a Alemanha, focado no portal DAAD.

Fontes utilizadas:
  - DAAD Scholarship Database (https://www.daad.de)
  - Scholarshipportal.com (fallback)
  - Fundação Alexander von Humboldt (AvH)

Estratégia de scraping:
  O DAAD utiliza renderização parcial via JavaScript, mas a maior parte do
  conteúdo da listagem está disponível no HTML inicial ou via parâmetros de
  URL. O scraper tenta:
    1. Acessar a listagem paginada do DAAD com filtro para a Alemanha
    2. Extrair cards de bolsas (nome, valor, prazo, área, tipo, link)
    3. Acessar cada página de detalhe para extrair requisitos e descrição
    4. Fallback: dados de bolsas conhecidas caso o site esteja bloqueado
"""

import sys
import os
import time
import re
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Services.university import Scholarship

# Configurações

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) "
        "Gecko/20100101 Firefox/120.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.daad.de/en/",
}

REQUEST_DELAY = 2.0  # segundos entre requisições

# URL de busca do DAAD (bolsas para estudar na Alemanha, em inglês)
DAAD_LISTING_URL = (
    "https://www.daad.de/en/study-and-research-in-germany/scholarships/"
    "scholarship-database/"
    "?origin=396&subjectGrpId=0&langAbroad=en&scholarship=0"
    "&langCode=en&cert=&admReq=&studyType=&countryInst=276"
    "&tyi%5B%5D=1&tyi%5B%5D=4&tyi%5B%5D=5"
    "&daad=0&intention=34&sort=4&page={page}"
)

# Dados de fallback — bolsas bem documentadas e públicas
# Usados quando o site retorna 403 ou não contém dados parseáveis.

FALLBACK_SCHOLARSHIPS = [
    {
        "name": "DAAD Scholarships for Foreign Students (Doctoral)",
        "value": "~€1.200/month + travel allowance + health insurance",
        "date": "October–November (for the following year)",
        "about": (
            "The DAAD (German Academic Exchange Service) offers scholarships "
            "for highly qualified international students and researchers to "
            "undertake doctoral studies or postdoctoral research at German "
            "higher education institutions."
        ),
        "requirements": (
            "Above-average academic record; Bachelor's or Master's degree "
            "relevant to the intended research topic; language skills in German "
            "or English depending on the program; research/project proposal; "
            "two academic letters of recommendation."
        ),
        "area": "All disciplines",
        "type": "Doctoral / Postdoctoral",
        "site": "https://www.daad.de/en/study-and-research-in-germany/scholarships/",
    },
    {
        "name": "DAAD Study Scholarship (Master's)",
        "value": "~€934/month + travel allowance + study/research allowance",
        "date": "November 15 (for the following academic year)",
        "about": (
            "Supports foreign graduates wishing to complete a full Master's "
            "degree program at a state or state-recognized German university. "
            "Open to candidates from all countries and all subject areas."
        ),
        "requirements": (
            "Bachelor's degree with above-average grades; minimum 2 years of "
            "professional experience after first degree; language proficiency "
            "(German B2 or English B2 depending on program); motivation letter; "
            "CV; two academic recommendations."
        ),
        "area": "All disciplines",
        "type": "Master's",
        "site": "https://www.daad.de/en/study-and-research-in-germany/scholarships/daad-scholarships/",
    },
    {
        "name": "Deutschland Stipendium (National Scholarship Programme)",
        "value": "€300/month (€150 from federal government + €150 from private donors)",
        "date": "Varies by university – typically March–May",
        "about": (
            "The Deutschlandstipendium is a national scholarship programme that "
            "supports talented and high-achieving students at German universities. "
            "Each scholarship is co-funded by private sponsors and the German federal "
            "government. Available at LMU, TUM, Humboldt and other German universities."
        ),
        "requirements": (
            "Enrollment or imminent enrollment at a German university; outstanding "
            "academic performance; social commitment and voluntary work; "
            "overcoming personal hardship or special social circumstances may "
            "also be considered. Application via the respective university portal."
        ),
        "area": "All disciplines",
        "type": "Undergraduate / Master's / Doctoral",
        "site": "https://www.deutschlandstipendium.de/en/",
    },
    {
        "name": "Alexander von Humboldt Foundation – Humboldt Research Fellowship",
        "value": "~€2.670/month (postdoctoral) or ~€3.170/month (experienced researchers) + additional allowances",
        "date": "Applications accepted year-round (no deadline)",
        "about": (
            "The Humboldt Research Fellowship allows highly qualified scientists "
            "and scholars from abroad to spend 6–24 months conducting independent "
            "research at German research institutions. The fellowship is particularly "
            "competitive and prestigious, connecting fellows to a global network of "
            "Humboldt Alumni."
        ),
        "requirements": (
            "Completed doctoral degree; above-average qualifications; research "
            "proposal; invitation or agreement from a German host researcher; "
            "strong publication record; language skills in German or English."
        ),
        "area": "All disciplines (natural sciences, engineering, humanities, social sciences)",
        "type": "Postdoctoral / Research",
        "site": "https://www.humboldt-foundation.de/en/apply/sponsorship-programmes/humboldt-research-fellowship",
    },
    {
        "name": "Bavarian State Government Scholarship (BayBFG) – LMU & TUM focus",
        "value": "Up to €3.600/year",
        "date": "Usually September–October for winter semester",
        "about": (
            "The Free State of Bavaria offers scholarships to outstanding "
            "international students enrolled at Bavarian universities, including "
            "LMU Munich and TUM. The scholarship supports academic excellence and "
            "integration into Bavarian academic culture."
        ),
        "requirements": (
            "Enrollment at a Bavarian public university (LMU or TUM); excellent "
            "academic record (typically top 5%); financial need; language proficiency "
            "in German; application submitted through the respective university's "
            "international office."
        ),
        "area": "All disciplines",
        "type": "Undergraduate / Master's",
        "site": "https://www.lmu.de/en/study/during-your-studies/financing-and-scholarships/",
    },
    {
        "name": "Heinrich Böll Foundation Scholarship",
        "value": "€861/month (Master's) or €1.350/month (Doctoral) + €300 book allowance",
        "date": "March 1 and September 1 (twice per year)",
        "about": (
            "The Heinrich Böll Foundation, affiliated with the German Green Party, "
            "supports students and doctoral candidates who show outstanding academic "
            "performance and commitment to green/ecological politics, gender democracy "
            "and human rights. Open to international students studying in Germany."
        ),
        "requirements": (
            "Enrollment or admission at a German university; above-average academic "
            "performance; sociopolitical engagement; affinity with the foundation's "
            "values (ecology, democracy, solidarity); written application, CV, "
            "and recommendation letters."
        ),
        "area": "All disciplines (focus on social sciences, humanities, environmental studies)",
        "type": "Master's / Doctoral",
        "site": "https://www.boell.de/en/foundation/scholarships",
    },
    {
        "name": "KAAD Scholarship (Catholic Academic Exchange Service)",
        "value": "€750–€1.050/month depending on study level",
        "date": "January 31",
        "about": (
            "KAAD promotes academic exchange between Germany and countries in "
            "Africa, Asia, Latin America, and the Middle East/North Africa. "
            "It supports Catholic students and scholars from these regions who "
            "wish to study or conduct research at German universities."
        ),
        "requirements": (
            "Catholic faith; citizenship of an eligible country (Africa, Asia, "
            "Latin America, MENA); admission to a German university; strong "
            "academic record; motivation for academic and social commitment in "
            "the home country after graduation."
        ),
        "area": "All disciplines",
        "type": "Master's / Doctoral",
        "site": "https://www.kaad.de/en/scholarships/",
    },
]

# Helpers

def get(url: str, timeout: int = 15) -> requests.Response | None:
    time.sleep(REQUEST_DELAY)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp
    except requests.RequestException as exc:
        print(f"  [WARN] Falha ao acessar {url}: {exc}")
        return None


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

# Scraping: DAAD listing page

def scrape_daad_listing(max_pages: int = 3) -> list[dict]:
    """
    Percorre a listagem paginada do DAAD e retorna uma lista de dicts
    com dados parciais de cada bolsa (nome, link, tipo, área).
    """
    raw_scholarships = []

    for page in range(1, max_pages + 1):
        url = DAAD_LISTING_URL.format(page=page)
        print(f"  → DAAD página {page}: {url[:80]}...")
        resp = get(url)

        if not resp:
            print(f"    [WARN] Página {page} inacessível.")
            break

        soup = BeautifulSoup(resp.text, "lxml")

        # Os cards de bolsas no DAAD ficam em <article> ou <div> com classes específicas
        cards = soup.find_all("article", class_=re.compile(r"scholarship|teaser|item", re.I))
        if not cards:
            # Tenta seletor alternativo
            cards = soup.find_all("div", class_=re.compile(r"scholarship|teaser-content|item", re.I))

        if not cards:
            print(f"    [WARN] Nenhum card encontrado na página {page}.")
            # Pode ser que a página seja renderizada via JS; tenta parsear qualquer <h2>/<h3>
            headings = soup.find_all(["h2", "h3"], class_=re.compile(r"title|heading|name", re.I))
            for h in headings:
                a = h.find("a")
                if a and a.get("href"):
                    raw_scholarships.append({
                        "name": clean(h.get_text()),
                        "link": a["href"] if a["href"].startswith("http") else f"https://www.daad.de{a['href']}",
                    })
            break

        print(f"    ✓ {len(cards)} cards encontrados.")
        for card in cards:
            name_tag = card.find(["h2", "h3", "h4"])
            link_tag = card.find("a", href=True)
            name = clean(name_tag.get_text()) if name_tag else "N/A"
            link = link_tag["href"] if link_tag else ""
            if link and not link.startswith("http"):
                link = f"https://www.daad.de{link}"

            # Tipo de bolsa
            type_tag = card.find(class_=re.compile(r"type|category|badge", re.I))
            scholarship_type = clean(type_tag.get_text()) if type_tag else "N/A"

            raw_scholarships.append({"name": name, "link": link, "type": scholarship_type})

    return raw_scholarships

# Scraping: DAAD detail page

def scrape_daad_detail(url: str) -> dict:
    """
    Acessa a página de detalhe de uma bolsa DAAD e extrai:
    value, date, about, requirements, area.
    """
    resp = get(url)
    if not resp:
        return {}

    soup = BeautifulSoup(resp.text, "lxml")
    data = {}

    # Valor da bolsa
    for label in soup.find_all(string=re.compile(r"value|amount|stipend|monthly", re.I)):
        parent = label.find_parent()
        if parent:
            sibling = parent.find_next_sibling()
            if sibling:
                data["value"] = clean(sibling.get_text())
                break

    # Data limite
    for label in soup.find_all(string=re.compile(r"deadline|application date|closing date", re.I)):
        parent = label.find_parent()
        if parent:
            sibling = parent.find_next_sibling()
            if sibling:
                data["date"] = clean(sibling.get_text())
                break

    # Descrição (about)
    about_section = soup.find(["div", "section"], class_=re.compile(r"description|about|content|text", re.I))
    if about_section:
        paragraphs = about_section.find_all("p")
        data["about"] = " ".join(clean(p.get_text()) for p in paragraphs[:3])

    # Requisitos
    req_section = soup.find(["div", "section"], class_=re.compile(r"requirement|eligib|criteria", re.I))
    if not req_section:
        req_section = soup.find(string=re.compile(r"requirement|eligib", re.I))
        if req_section:
            req_section = req_section.find_parent(["div", "section", "article"])

    if req_section:
        items = req_section.find_all("li")
        if items:
            data["requirements"] = "; ".join(clean(i.get_text()) for i in items[:6])
        else:
            data["requirements"] = clean(req_section.get_text())[:400]

    # Área
    for label in soup.find_all(string=re.compile(r"subject|field|area|discipline", re.I)):
        parent = label.find_parent()
        if parent:
            sibling = parent.find_next_sibling()
            if sibling:
                data["area"] = clean(sibling.get_text())
                break

    return data

# Função principal: scraping de bolsas

def scrape_scholarships(max_scholarships: int = 7) -> list[Scholarship]:
    """
    Coleta bolsas disponíveis para a Alemanha via DAAD e retorna
    uma lista de objetos Scholarship.

    Se o site DAAD estiver inacessível, retorna dados de fallback
    com as bolsas mais relevantes já documentadas.
    """
    print("\n" + "="*60)
    print("Coletando bolsas (DAAD + outras fontes)...")
    print("="*60)

    scholarships = []

    # --- Tentativa de scraping ao vivo ---
    raw = scrape_daad_listing(max_pages=2)

    if raw:
        print(f"\n  ✓ {len(raw)} bolsas encontradas na listagem DAAD.")
        for item in raw[:max_scholarships]:
            print(f"  → Detalhes: {item.get('name', 'N/A')[:50]}...")
            details = {}
            if item.get("link"):
                details = scrape_daad_detail(item["link"])

            scholarships.append(Scholarship(
                name=item.get("name", "N/A"),
                value=details.get("value", "See DAAD website"),
                date=details.get("date", "See DAAD website"),
                about=details.get("about", "See DAAD website for full description."),
                requirements=details.get("requirements", "See DAAD website for eligibility criteria."),
                area=details.get("area", item.get("area", "All disciplines")),
                type=details.get("type", item.get("type", "N/A")),
                site=item.get("link", "https://www.daad.de/en/"),
            ))
    else:
        # --- Fallback com dados confiáveis já documentados ---
        print("\n  [INFO] DAAD ao vivo inacessível. Usando dados de referência documentados.")
        for s in FALLBACK_SCHOLARSHIPS[:max_scholarships]:
            scholarships.append(Scholarship(
                name=s["name"],
                value=s["value"],
                date=s["date"],
                about=s["about"],
                requirements=s["requirements"],
                area=s["area"],
                type=s["type"],
                site=s["site"],
            ))

    print(f"\n  ✓ {len(scholarships)} bolsas coletadas.")
    return scholarships

# Execução direta (teste)

if __name__ == "__main__":
    results = scrape_scholarships()

    print("\n\n" + "="*60)
    print("BOLSAS COLETADAS")
    print("="*60)
    for s in results:
        print(f"\n{s.name}")
        print(f"  Valor      : {s.value}")
        print(f"  Prazo      : {s.date}")
        print(f"  Área       : {s.area}")
        print(f"  Tipo       : {s.type}")
        print(f"  Sobre      : {s.about[:100]}...")
        print(f"  Requisitos : {s.requirements[:100]}...")
        print(f"  Site       : {s.site}")

