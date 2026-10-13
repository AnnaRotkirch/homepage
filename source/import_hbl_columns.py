#!/usr/bin/env python3
"""Import Anna Rotkirch's Hbl "I dag" columns (Swedish, 2013-2023) from her manuscript folder
into content/columns/*.md.

Usage:  python3 import_hbl_columns.py "<path to 'kolumner 2012-' folder>"

Reads each manuscript listed in COLUMNS below (.docx; .doc is converted with LibreOffice first),
converts it with pandoc (tracked changes accepted), removes working labels, bio lines and
sign-offs, and writes one file per column to ../content/columns/ (resolved from this script's
location). The manuscript folder is only read, never changed.

Selection (2026-10-13, Anna's instruction): Swedish columns only; Finnish texts and files named
"ta inte" are left out; drafts, notes and non-Hbl texts are left out (see EXCLUDED).
Dates are approximate (Anna: about one column a month): the month in the file name, else the
month the manuscript was last saved. Titles are the manuscript's own heading; where the
manuscript has none, the title of the same text on her old blog is used (TITLE_FROM_OLD_BLOG).
Requires pandoc (and soffice for .doc).
"""
import os, re, sys, subprocess, tempfile, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "content", "columns")

# file name -> (title, date). title None = the first heading line of the manuscript.
COLUMNS = {
    "Tråkigt är bäst.docx": (None, "2013-03"),
    "Ingen panik.docx": (None, "2013-04"),
    "hbl rysk homofobi.docx": (None, "2013-05"),
    "Miraklet förklarats.docx": (None, "2013-06"),
    "På stående fot.docx": (None, "2013-08"),
    "hbl För gammal mamma.docx": (None, "2013-10"),
    "Lessing in memoriam.docx": (None, "2013-11"),
    "Fången och presidenten.docx": (None, "2013-12"),
    "Är Finland kristet.docx": (None, "2014-04"),
    "Hbl efter familjepaketet.docx": (None, "2015-02"),
    "Hbl mars 2015 telefoner.docx": (None, "2015-03"),
    "Hbl april 2015.docx": (None, "2015-04"),
    "Hbl maj 2015 Kon som försvann.docx": (None, "2015-05"),
    "Hbl juni 2015 Strömsö.docx": (None, "2015-06"),
    "Hbl juli 2015 Läsning för barn.docx": (None, "2015-07"),
    "hbl okt 2015 recession Christopher Whelan.docx": (None, "2015-10"),
    "Hbl nov 2015 Gawande kort.docx": (None, "2015-11"),
    "Hbl december 2015 Kan vänner ersätta syskon.docx": (None, "2015-12"),
    "Hbl januari 2016 För många män.docx": (None, "2016-01"),
    "Hbl februari 2016 Giftas.docx": (None, "2016-02"),
    "Hbl april 2016 Engelsk rysare.docx": (None, "2016-04"),
    "Hbl maj 2016 Gruppens vilsenhet.docx": (None, "2016-05"),
    "Hbl juni 2016 Vargen i bryggerikläder.docx": ("Vargen i bryggerikläder", "2016-06"),   # Anna: title is the file name, not the heading "WOW"
    "Hbl Pokemon rättad jul 2016.docx": (None, "2016-07"),
    "hbl aug 2016 kreml.docx": (None, "2016-08"),
    "Hbl september 2016 Om Jimi inte dött.docx": (None, "2016-09"),
    "Barn hjärta hbl oktober 2016.docx": (None, "2016-10"),
    "Hbl december 2016 Ylegate.docx": (None, "2016-12"),
    "Hbl februari 2017 Den dagen kändes det som om allt rasade samman.docx": (None, "2017-02"),
    "Hbl april migration kortare1.docx": (None, "2017-04"),
    "Hbl juni 2017 motståndet.docx": (None, "2017-06"),
    "Hbl augusti 2017 sverige.docx": (None, "2017-08"),
    "Hbl september 2017 hur 3D printern räddar liv.docx": (None, "2017-09"),
    "Hbl okt 2017.docx": (None, "2017-10"),
    "Hbl november 2017 trakasserier.docx": (None, "2017-11"),
    "Hbl dofternas högtid dec 2017.docx": (None, "2017-12"),
    "Hbl moskvaskola hbl februari 2018.docx": (None, "2018-02"),
    "Entimmesregeln hbl mars 2018.docx": (None, "2018-03"),
    "Tänk först testa sedan hbl april 2018.docx": (None, "2018-04"),
    "Könen i skolböcker hbl maj 2018.docx": (None, "2018-05"),
    "baby bust hbl juni 2018.docx": (None, "2018-06"),
    "hbl neandertalarfamilj juni 2018.docx": (None, "2018-06"),   # Anna 2026-10-13: add, "it is a blog"
    "Attraktiv ankdamm hbl juli 2018.docx": (None, "2018-07"),
    "När kvinnor trakasserar hbl aug 2018.docx": (None, "2018-08"),
    "Hbl telefoner 2018 Men om jag nu ska skriva den här kolumnen så får det inte bli vad du tycker.docx": (None, "2018-10"),
    "Hbl nov 2018 För många jobb i världen.docx": (None, "2018-11"),
    "Brexitbrev hbl dec 2018.docx": (None, "2018-12"),
    "hbl jan 2019 Apelsinskalet i spottkoppen.docx": (None, "2019-01"),
    "hbl mars 2019 Är större alltid bättre.docx": (None, "2019-03"),
    "Hbl christ church skjutning 2018.docx": (None, "2019-03"),   # labelled "Hbl I dag kolumn 2019"
    "Kärlek på äldre dagar hbl april 2019.docx": (None, "2019-04"),
    "Europas Japan hbl maj 2019.docx": (None, "2019-05"),
    "Stoppminkropp juli 2019.docx": (None, "2019-07"),
    "Pulu aug 2019.docx": (None, "2019-08"),
    "Stockmann hbl sept 2019.docx": (None, "2019-09"),
    "hbl okt 2019 Babyn och klimatet.docx": (None, "2019-10"),
    "hbl nov 2019 mobiler bystander.docx": (None, "2019-11"),
    "hbl dec 2019 go boomer.docx": (None, "2019-12"),
    "Våga säga baby hbl januari 2020.docx": (None, "2020-01"),
    "Hbl befolkningsprognoser juli 2020.docx": (None, "2020-07"),
    "hbl Andra våg eller egen båt augusti 2020.docx": (None, "2020-08"),
    "hbl Skräddaren och guldsmeden oktober 2020.docx": ("Skräddaren och guldsmeden", "2020-10"),
    "hbl Pandemi baby bust nov 2020.docx": (None, "2020-11"),
    "Hbl dec 2020.docx": (None, "2020-12"),
    "Hbl dec 2020 vackra 2020.docx": (None, "2020-12"),
    "hbl utlands.docx": (None, "2021-01"),
    "Hbl feb 21 plantor.docx": (None, "2021-02"),
    "hbl mars utredning 2021.docx": (None, "2021-03"),
    "Masknationalismens tre orsaker april 2021.docx": (None, "2021-04"),
    "Rom öppnare stad juni 2021.docx": (None, "2021-06"),
    "hbl suzman klein juli 2021.docx": (None, "2021-07"),
    "hbl negationer sept 2021.docx": (None, "2021-09"),
    "When i'm 64 hbl okt 2021.docx": (None, "2021-10"),
    "hbl november 2021 Ju äldre du blir.docx": (None, "2021-11"),
    "hbl december 2021 Julsaga hbl rotkirch.docx": (None, "2021-12"),
    "hbl januari 2022 Vi slåss mot viruset hbl.docx": ("Vi slåss mot viruset", "2022-01"),
    "hbl februari 2022 psykiskt välbefinnande del 2 ny.docx": (None, "2022-02"),
    "hbl mars 2022 ukraina i europa hbl.docx": (None, "2022-03"),
    "Hbl april 2022 superryss.docx": (None, "2022-04"),
    "Hbl armotonta menoa april 2022.docx": (None, "2022-04"),
    "Hbl maj 2022 fruktsamhet.docx": (None, "2022-05"),
    "Hbl åldrande befolkning kort juli 2022.docx": (None, "2022-07"),
    "hbl augusti 2022 Minska mattan kort.docx": (None, "2022-08"),
    "Hbl september 2022 Imperiets sista strid final.docx": (None, "2022-09"),
    "Hbl october 2022 tid.docx": (None, "2022-10"),
    "hbl nov 2022 gårdsbacka etnicitet.docx": (None, "2022-11"),
    "Hbl februari 2013 Dans Iran.docx": (None, "2023-02"),   # file name says 2013; text and save date are 2023
    "Hbl mars 2023 sista hålls gift.docx": (None, "2023-03"),
}
# Already on the site from the old blog (Anna 2026-10-13): the old-blog text is kept and only its
# date is set from the Hbl manuscript, so these are NOT imported here: HBl I dag Töttö,
# Faderskapsledighet hbl, Forngravar hbl, Finland har mest omhändertagna…, HBL mars, Familjers
# vardag hbl, De förstföddas…, MH17…, hbl september, Skuggan, Varför ökar barnlösheten…,
# HBl november 2014 lek, Hbl jan 2015, Hbl sept 2015 hatretorik.
# Titles taken from the old blog, where the manuscript has no heading (same text, checked):
# Finland har mest… -> De mest omhändertagna; HBL mars -> Tyrannens namn; Familjers vardag hbl ->
# Skör balans i familjepolitiken; HBl november 2014 lek -> Skratt, flit och galna idéer;
# Hbl jan 2015 -> Lycklig, älskad, rik?  Other overrides: "Skräddaren och guldsmede" (manuscript
# typo, file name has guldsmeden); "Vi slåss mot viruset" (no heading; title from file name).

BLOG = {"hbl neandertalarfamilj juni 2018.docx"}   # Anna: a blog text, not an I dag column

LABEL = re.compile(r"(?i)^(hbl|hbl i dag|hbl debatt)\b.{0,40}$")          # "Hbl dec 2020", "HBL augusti"
BIO = re.compile(r"^\[*Anna Rotkirch\b")                                  # bio line or sign-off

def to_markdown(path):
    if path.endswith(".doc"):
        tmp = tempfile.mkdtemp()
        subprocess.run(["soffice", "--headless", "--convert-to", "docx", "--outdir", tmp, path],
                       check=True, capture_output=True)
        path = os.path.join(tmp, os.path.basename(path) + "x")
    return subprocess.run(["pandoc", path, "-t", "markdown-smart", "--wrap=none",
                           "--track-changes=accept"], check=True, capture_output=True,
                          text=True).stdout

def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60].strip("-")

def clean(md, title):
    paras = [p.strip() for p in md.split("\n\n") if p.strip()]
    paras = [re.sub(r"\[([^\]]*)\]\{\.[a-z]+\}", r"\1", p) for p in paras]   # pandoc spans
    note = None
    # leading working labels, bio lines and datelines like "Hbl I dag 7.9, http://…"
    while paras and (LABEL.match(paras[0]) or BIO.match(paras[0])
                     or re.match(r"^(är|forskn\w*) ", paras[0]) or "http://hbl.fi" in paras[0]):
        if "dagsverkade" in paras[0]:
            note = paras[0]
        paras.pop(0)
    if title is None:
        title = paras.pop(0).strip("*")
    elif paras and title.startswith(paras[0].strip("*")):
        paras.pop(0)
    while paras and (LABEL.match(paras[0]) or BIO.match(paras[0]) or "http://hbl.fi" in paras[0]):
        if "dagsverkade" in paras[0]:
            note = paras[0]
        paras.pop(0)
    # trailing sign-off: "Anna Rotkirch" (+ "är forskningsprofessor…") or a stray "." / "Anna"
    while paras and (BIO.match(paras[-1]) or paras[-1] in (".", "Anna", " ")
                     or (len(paras) > 1 and BIO.match(paras[-2]) and len(paras[-1]) < 120)):
        paras.pop()
    # Jul i norr: paragraph initials spell GLAD JUL, set with a space after the letter
    acrostic = sum(bool(re.match(r"^[A-ZÅÄÖ] [a-zåäö]", p)) for p in paras) >= 5
    out = []
    for p in paras:
        if re.fullmatch(r"/[^/]+/", p):        # editor's instruction, e.g. "/mellanrad tom/"
            continue
        if p == r"-   \*":
            out.append("\\* \\* \\*"); continue
        p = re.sub(r"^-   ", "– ", p)          # dialogue lines that Word turned into bullets
        p = re.sub(r"^\\- ", "– ", p)
        p = re.sub(r"^#", r"\\#", p)            # "#Metoo" at line start is not a heading
        if acrostic:
            p = re.sub(r"^([A-ZÅÄÖ]) ([a-zåäö])", r"**\1**\2", p)
        out.append(p)
    # the "dagsverkade" header line of Mobilförbud i skolan? is not printed: Anna is the author
    return title, "\n\n".join(out)

def main(src):
    os.makedirs(OUT, exist_ok=True)
    for f, (title, date) in COLUMNS.items():
        path = os.path.join(src, f)
        t, text = clean(to_markdown(path), title)
        name = f"{date}-{slugify(t)}.md"
        kind = "blog" if f in BLOG else "I dag"
        head = (f"title: {t}\ndate: {date}\nlang: sv\noutlet: hbl\n"
                f"source: Hufvudstadsbladet, {kind} (manuscript: {f})\n")
        open(os.path.join(OUT, name), "w", encoding="utf-8").write(head + "\n" + text + "\n")
        print(name, len(text.split()))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
