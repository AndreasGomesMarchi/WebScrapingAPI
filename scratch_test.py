import requests
from bs4 import BeautifulSoup

urls = [
    "https://www.educanada.ca/scholarships-bourses/can/institutions/elap-pfla.aspx?lang=eng",
    "https://www.educanada.ca/scholarships-bourses/non_can/ccsep-peucc.aspx?lang=eng"
]

def get_section_text(soup, keywords):
    for tag in soup.find_all(['h2', 'h3', 'h4', 'strong', 'b', 'p']):
        text = tag.get_text(strip=True).lower()
        if any(key.lower() in text for key in keywords) and len(text) < 150:
            content = []
            
            # Sometimes the info is directly inside the tag if it's a p with strong
            if tag.name == 'p' and len(tag.get_text(strip=True)) > 50:
                 # Check if it has the actual content, not just the heading
                 content.append(tag.get_text(" ", strip=True))

            next_node = tag.find_next_sibling()
            if tag.name in ['strong', 'b'] and tag.parent:
                next_node = tag.parent.find_next_sibling()
                
            count = 0
            while next_node and count < 10:  # limit to prevent capturing the whole page
                if next_node.name in ['h2', 'h3', 'h4', 'h1']:
                    break
                
                # if we hit a p that is strongly formatted or short, it might be the next heading
                if next_node.name == 'p' and next_node.find('strong') and len(next_node.get_text(strip=True)) < 50:
                    break
                    
                if next_node.name in ['p', 'ul', 'ol', 'div', 'li']:
                    text_content = next_node.get_text(" ", strip=True)
                    if text_content:
                        content.append(text_content)
                next_node = next_node.find_next_sibling()
                count += 1
                
            res = " ".join(content).strip()
            if res:
                return res
    return "N/A"

for url in urls:
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    print(f"\n--- URL: {url} ---")
    
    about = get_section_text(soup, ["objectives", "description", "about"])
    reqs = get_section_text(soup, ["eligibility", "eligible"])
    val = get_section_text(soup, ["value", "amount"])
    date = get_section_text(soup, ["deadline", "key dates"])
    area = get_section_text(soup, ["fields", "area", "discipline"])
    
    print("ABOUT:", about[:200] + "..." if about != "N/A" else "N/A")
    print("REQS:", reqs[:200] + "..." if reqs != "N/A" else "N/A")
    print("VALUE:", val[:200] + "..." if val != "N/A" else "N/A")
    print("DATE:", date[:200] + "..." if date != "N/A" else "N/A")
    print("AREA:", area[:200] + "..." if area != "N/A" else "N/A")
