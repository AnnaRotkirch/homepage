import re, sys
src = open("source/publications_by_year_2026-09-14.md", encoding="utf-8").read()
# entries = paragraphs under any "## " heading except Current favourites
parts = re.split(r"^## ", src, flags=re.M)
fav = [p for p in parts if p.startswith("Current favourites")][0]
fav_entries = [e.strip() for e in fav.split("\n\n")[1:] if e.strip()]
entries = []
for p in parts[1:]:
    if p.startswith("Current favourites"): continue
    for e in p.split("\n\n")[1:]:
        if e.strip(): entries.append(e.strip())
print(len(entries), "entries", file=sys.stderr)

T = {}  # substring -> theme
def add(theme, *keys):
    for k in keys: T[k] = theme
add("Fertility",
    "Fertility trends across migrant", "timing of entry into parenthood", "Reasons to postpone childbearing",
    "Fertility recovery despite", "Social resources are associated with higher fertility",
    "Counting on parents or others", "Fertility resilience varies", "first Generations and Gender Survey",
    "Birth cohort changes in fertility ideals", "The wish for a child", "Financial opportunity costs",
    "Attitudes of anonymous and identity-release", "Childlessness in Finland", "Childlessness and assisted reproduction",
    "Short- and long-term health consequences", "Does domestic gender equality predict", "Faster transition to the second child",
    "Postponing births", "Increasing childlessness in Europe", "Baby fever and longing for children",
    "Baby longing and men", "Gender equality and fertility intentions", "All that she wants",
    "What is \"baby fever\"", "Urban residential clustering", "Maternal risk of breeding failure",
    "Two children puts you in the zone", "The first child is the fruit of love", "Chislo detej")
add("Families",
    "Widowhood and grandchild care", "In a society of strangers", "Changes in subjective wellbeing during widowhood",
    "Stable marital histories", "ageing women's sexual subjectivity", "Both partnership history",
    "Do working and parenting trajectories", "Effects of information and communication technology",
    "Parental relationships and family functioning", "Kin detection cues", "Shorter birth intervals",
    "Migration patterns of parents", "Sibling similarity", "Network of families", "kinship penalty",
    "Emotional closeness predicted", "Manipulative use of kin", "Diluted competition", "Sibling conflicts in full-",
    "impact of genetic relatedness", "Jollei minulla olisi sinua", "More unintended injuries",
    "Gratitude for help", "Associations between family size", "Maternal guilt", "Sexuality and family formation",
    "Sukupolvien ketju", "Yksin kotona", "Pirstoutunut vanhemmuus", "Ydin- ja versoperheet",
    "Effects of remarriage after widowhood")
add("Population policy and public health",
    "Future population ageing and productivity", "Face masks to prevent", "Universal masking",
    "How to use the maternity capital", "Who helps the degraded housewife", "Social consequences of the 1998 crisis")
add("Grandparents",
    "Partnership histories shape the grandparenting", "Grandparental investment in biological",
    "Grandparents look after", "Grandparental effects on fertility", "impact of grandparental investment",
    "Multipartner fertility", "Do grandparents favor granddaughters", "Grandparental child care in Europe")
add("Friendship and social networks",
    "Kinship and friendship networks", "Residential mobility and social capital",
    "Psychological and social wellbeing associated with regional", "Ystävät", "Social network complexity",
    "Fraternity ties", "Peer relations with mobile phone data", "The company you keep",
    "Life course similarities", "Singing together or apart", "Mistä on ystävyydet", "Women favour dyadic")
add("Evolutionary approaches",
    "Integration involves a trade-off", "Effects of female reproductive competition",
    "Evolutionary family sociology", "Costly reproductive competition", "Sukupuolet evoluutioteoriassa",
    "Mating strategies in Mozart", "Ihmisperhe evoluutiopsykologiassa", "Natural and sexual selection",
    "Serial monogamy", "Miten sosiologinen tieto", "Habitus, naturaleza", "Naturligtvis?")
add("Sexuality and gender",
    "Sexual therapists in Russia", "Здоровье, удовольствие", "Contradictory trends in sexual life",
    "What kind of sex can you talk about", "Sexuelle Lebensstile", "Sovetskie kul'tury seksual'nosti",
    "Loving with and without words", "Gender polarisation and liberalisation", "Traveling maidens",
    "Generational and gender differences in sexual life", "What does the (Russian) woman want",
    "Toiminta, reflektiivisyys")
add("Russia and post-Soviet society",
    "Making and managing class", "Vallankumouksen uusi nainen", "Uusien venäläisten", "Rakare, friare",
    "Sovetskie gendernye kontrakty i ih izmenenia", "Sauver ses fils", "New woman with old feelings",
    "Besputnaia zhizn", "Vem är rädd för städerskan", "Hva er tradisjonalisme",
    "Sovetskie gendernye kontrakty i ih transformatsiia", "Shame, promiscuity", "Nyt en aio lähteä",
    "Emma Goldman", "Skuggfält", "Soviet gender contracts and their shifts", "Hökkelit suuren joen",
    "The playing '80s", "Me muut")

groups = {}
for e in entries:
    hits = [t for k, t in T.items() if k in e]
    if len(set(hits)) != 1:
        print("UNASSIGNED" if not hits else "MULTI", hits, e[:90], file=sys.stderr); continue
    groups.setdefault(hits[0], []).append(e)
def year(e):
    m = re.search(r"\((\d{4})\)", e); return int(m.group(1)) if m else 0
for g in groups.values(): g.sort(key=year, reverse=True)

# extra items for Population policy (from books.md / About), as she asked
policy_extra = [
 "Rotkirch, A. (2024). *20 ehdotusta lapsitoiveiden tukemiseksi. Selvitys syntyvyyden laskusta Suomessa.* Valtioneuvoston julkaisuja 2025:22.",
 "Rotkirch, A. (2021). [*Population policy guidelines for the 2020s. Executive summary of the Finnish population policy report*](https://vnk.fi/documents/10616/78382279/vaestoselvitys_avainkohdat_VNK_2021_2_EN.pdf). Prime Minister's Office, Finland 2021:2. ([Finnish version](http://urn.fi/URN:ISBN:978-952-383-073-8))",
 "Rotkirch, A. (2020). [Declining birth rate and changing childbearing landscape](https://www.vaestoliitto.fi/en/webpublications/sustainable-population-development-in-finland/). In T. Sorsa (Ed.), *Sustainable Population Development in Finland: the 2020 population policy report by Väestöliitto*. Väestöliitto.",
]
pp = groups["Population policy and public health"] + policy_extra
pp.sort(key=year, reverse=True); groups["Population policy and public health"] = pp

MAIN = ["Fertility", "Families", "Population policy and public health", "Grandparents",
        "Friendship and social networks", "Evolutionary approaches"]
ARCH = ["Sexuality and gender", "Russia and post-Soviet society"]
def section(t): return f"## {t}\n\n" + "\n\n".join(groups[t]) + "\n\n"

main = ("# Publications\n"
 "description: Journal articles, chapters and working papers by Anna Rotkirch, grouped by theme, with links to the published versions.\n\n"
 "Articles, chapters and working papers by theme, most recent first within each theme. Books and reports have "
 "[their own page](books.html); earlier work on sexuality and on Russia is on the "
 "[archive page](archive.html).\n\n"
 "## Current favourites\n\n" + "\n\n".join(fav_entries) + "\n\n" + "".join(section(t) for t in MAIN))
arch = ("# Other and older publications\n"
 "description: Earlier publications by Anna Rotkirch on sexuality, gender and Russian society, 1996–2025.\n\n"
 "Earlier lines of work, by theme, most recent first. The main [Publications](publications.html) page "
 "holds current themes.\n\n" + "".join(section(t) for t in ARCH))
open("content/publications.md", "w", encoding="utf-8").write(main.rstrip("\n") + "\n")
open("content/archive.md", "w", encoding="utf-8").write(arch.rstrip("\n") + "\n")
for t in MAIN + ARCH: print(f"{len(groups[t]):3d}  {t}", file=sys.stderr)
