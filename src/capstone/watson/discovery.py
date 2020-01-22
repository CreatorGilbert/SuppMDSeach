from ibm_watson import DiscoveryV1
import json
import re
from pprint import pprint
from collections import defaultdict
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.corpus import wordnet


###
# Discovery API for scientific queries (Examine)
###
SCI_ENV = "e2b9a1a4-180b-4cf4-8ee1-48bd29c82ce1"
SCI_DB = "1e7d06a5-ab75-4374-8a25-0fcba03bec61"
SCI_V = "2019-04-30"
SCI_KEY = "_ofHkurx7vJ4HkXwwWi5TCMgNEPH0SfQVqL8s1v27QP4"
SCI_URL = "https://gateway.watsonplatform.net/discovery/api"

###
# Discovery API for "alternative" queries (forums, reddit, etc.)
###
ALT_ENV = "4ac63b11-3875-40ea-a186-c01d304d50d3"
# Config ID 679beef1-70fd-4c62-b251-b40169a1dce3
ALT_DB = "d99acd00-ac6d-4ba3-a2ec-cbec3dbf739c"
ALT_V = "2019-04-30"
ALT_KEY = "4e1xEPPR23PHxGjRL8P5KyTxdeHmPYH3pXy2q0KLrNge"
ALT_URL = "https://gateway.watsonplatform.net/discovery/api"

###
# Discovery API
###
DY_SCI = DiscoveryV1(version=SCI_V, iam_apikey=SCI_KEY, url=SCI_URL)
# DY_ALT = DiscoveryV1(version=SCI_V, iam_apikey=SCI_KEY, url=SCI_URL)
DY_ALT = DiscoveryV1(version=ALT_V, iam_apikey=ALT_KEY, url=ALT_URL)

fields_dic = DY_SCI.list_collection_fields(f"{SCI_ENV}", f"{SCI_DB}").get_result()[
    "fields"
]

examine_fields = []
for f in fields_dic:
    examine_fields.append(f["field"])

supplements = []
for p in examine_fields:
    supplements.append(p.split("/")[-1])

def get_suppliments():
    return supplements

###
# HIGHLIGHTING
###
def generate_terms(wordlist):
    stop_words = set(stopwords.words("english"))
    filtered = set()
    res = set()
    for w in wordlist:
        if w.lower() not in stop_words:
            filtered.add(w)
    for f in filtered:
        res.add(f)
        ss = wordnet.synsets(f)
        for word in ss:
            res = res.union(set(list(word.lemma_names())))
    return res


###
# END HIGHLIGHTING
###


def discover_nlp(api, query, env, dataset, keywords, get_text):
    """returns the result of an nlp query"""
    return api.query(
        environment_id=env,
        collection_id=dataset,
        passages_count=10,
        natural_language_query=query,
        passages=get_text,
        passages_characters=300,
        passages_fields=",".join(keywords),
    ).get_result()


def discover_qlang(api, query, env, dataset, get_text):
    """returns the result of a discovery language query"""
    return api.query(
        environment_id=env, collection_id=dataset, query=query, passages=get_text
    ).get_result()


# I think this works
def discover_doc(query, use_nlp=True):
    examine_keywords = get_examine_keywords(query)
    pprint(examine_keywords)
    if use_nlp:
        response_sci = discover_nlp(
            DY_SCI, query, SCI_ENV, SCI_DB, examine_keywords, False
        )
        response_alt = discover_nlp(DY_ALT, query, ALT_ENV, ALT_DB, "", False)
        # response_alt = discover_nlp(DY_SCI, query, SCI_ENV, SCI_DB, examine_keywords, False)
    else:
        response_sci = discover_qlang(DY_SCI, query, SCI_ENV, SCI_DB, False)
        response_alt = discover_qlang(DY_ALT, query, ALT_ENV, ALT_DB, False)

    result = dict.fromkeys("SCI", "ALT")

    result["SCI"] = parse_doc(response_sci)
    result["ALT"] = parse_doc(response_alt)

    return result


def discover(query, use_nlp=True, get_text=True):
    """returns scientific and alternative information from the Discovery API"""

    examine_keywords = get_examine_keywords(query)
    pprint(examine_keywords)
    if use_nlp:
        response_sci = discover_nlp(
            DY_SCI, query, SCI_ENV, SCI_DB, examine_keywords, get_text
        )
        response_alt = discover_nlp(DY_ALT, query, ALT_ENV, ALT_DB, "", get_text)
        # response_alt = discover_nlp(DY_SCI, query, SCI_ENV, SCI_DB, examine_keywords, get_text)
    else:
        response_sci = discover_qlang(DY_SCI, query, SCI_ENV, SCI_DB, get_text)
        response_alt = discover_qlang(DY_ALT, query, ALT_ENV, ALT_DB, get_text)
    seq = ("SCI", "ALT")
    result = dict.fromkeys(seq)

    if get_text:
        result["SCI"] = build_text(response_sci, query, True)
        result["ALT"] = build_text(response_alt, query, False)
    else:
        result["SCI"] = response_sci
        result["ALT"] = response_alt

    return result


def get_examine_keywords(query):
    keywords = []
    for s in supp_list:
        if s in query:
            keywords.append(s)

    return keywords


# https://cloud.ibm.com/apidocs/discovery?code=python#query-a-collection
def parse_doc(response):
    psg = []
    for r in response["results"]:
        res = r.metadata.split("##~~##~~##~~##~~##~~##~~##")
        for re in res:
            if re:
                psg.append(re)
    return psg


def build_text(response, query, examine):
    """returns a list of passages from the Discovery API response"""
    syns = generate_terms(word_tokenize(query))
    psg = []
    resp = response["passages"]
    if not examine:
            resp.sort(key=lambda x: len(x["passage_text"]), reverse=True)
    res_list = response["results"]
    p1 = " https://www.examine.com"
    x = 0
    for r in resp:
        if x == 5:
            break;
        psg_url = ""
        doc_id = r["document_id"]
        # psg[#][0] = passage text and psg[#][1] = url
        txt = r["passage_text"]
        # use txt, need to replace words given with span tag with the txt file
        # need txt file, a hash with the words and passage
        for word in syns:
            txt = re.sub(r"\b" + word.upper() + r"\b", "<mark>" + word.title() + "</mark>", txt)
            txt = re.sub(r"\b" + word.title() + r"\b", "<mark>" + word.title() + "</mark>", txt)
            txt = re.sub(r"\b" + word + r"\b", "<mark>" + word + "</mark>", txt)
        txt = add_definition(txt)
        if "=====" in txt:
            split = txt.split("=====")
            for st in split:
                if st and len(st) > 50:
                    for ree in res_list:
                        if ree["id"] in doc_id and not examine:
                            psg.append([st, ree["url"]])
        else:
            for ree in res_list:
                if ree["id"] in doc_id and not examine:
                        psg_url = ree["url"]
                        break;

            psg.append([txt, psg_url if psg_url else re.sub(r"examine", p1, r["field"])])
        x += 1
    return psg

def add_definition(paragraph):
    a1 = {}
    a1['kidney'] = "Either one of a pair of organs in the dorsal region of the vertebrate abdominal cavity, functioning to maintain proper water and electrolyte balance, regulate acid-base concentration, and filter the blood of metabolic wastes, which are then excreted as urine."
    a1['HMB'] = "A nitrogenous organic acid, C4H9N3O2, that is found in the muscle tissue of vertebrates mainly in the form of phosphocreatine and supplies energy for muscle contraction."
    a1['function'] = "something who knows"
    for key, value in a1.items():
        paragraph = re.sub(r""+key, "<span class=\"tooltip1\">"+key+"<span class=\"tooltiptext1\">"+value+"</span></span>", paragraph,  flags=re.IGNORECASE)
    return paragraph

# def add_definition(paragraph, dictionary):
#     for key, value in dictionary.items():
#         paragraph = re.sub(r""+key, "<span class=\"tooltip\">"+key+"<span class=\"tooltiptext\">"+value+"</span></span>", paragraph)
#     return paragraph

supp_list = [
"1,3-Dimethylamylamine",
"2,4-Dinitrophenol",
"5-HTP",
"7,8-Dihydroxyflavone",
"7-Keto DHEA",
"Acorus calamus",
"Adrafinil",
"Aframomum melegueta",
"Agmatine",
"Alanine",
"Alanylglutamine",
"Alcohol",
"Aloe vera",
"Alpha-GPC",
"Alpha-Lipoic Acid",
"Amaranth",
"Anacyclus pyrethrum",
"Anatabine",
"Anchor",
"Andrographis paniculata",
"Anethum graveolens",
"Angelica gigas",
"Aniracetam",
"Apigenin",
"Apocynum venetum",
"Arachidonic acid",
"Arginine",
"Aromatherapy",
"Aronia melanocarpa",
"Artemisia iwayomogi",
"Artichoke Extract",
"Ascophyllum nodosum",
"Ashwagandha",
"Asparagus racemosus",
"Astaxanthin",
"Asteracantha longifolia",
"Astragalus membranaceus",
"Ayurveda",
"BPC-157",
"Bacopa monnieri",
"Banaba Leaf",
"Basella alba",
"Beet Root",
"Benfotiamine",
"Berberine",
"Beta-Alanine",
"Betalains",
"Biotin",
"Black Cohosh",
"Black Pepper",
"Bladderwrack",
"Blueberry",
"Boerhaavia diffusa",
"Boron",
"Boswellia serrata",
"Branched Chain Amino Acids",
"Brassaiopsis glomerulata",
"Brassica vegetables",
"Brassinosteroids",
"Bromelain",
"Bryonia laciniosa",
"Bulbine natalensis",
"Butea monosperma",
"Butea superba",
"CBD",
"CDP-choline",
"Caesalpinia benthamiana",
"Caffeine",
"Calcium",
"Calcium-D-Glucarate",
"Capsaicin",
"Capsicum Carotenoids",
"Caralluma fimbriata",
"Casein Protein",
"Celastrus paniculatus",
"Celery seed extract",
"Centella asiatica",
"Centrophenoxine",
"Chlorella",
"Chlorogenic Acid",
"Chlorophytum borivilianum",
"Choline",
"Chondroitin",
"Chromium",
"Chrysin",
"Cinnamon",
"Cissus quadrangularis",
"Citric Acid",
"Citrulline",
"Citrullus colocynthis",
"Clenbuterol",
"Clitoria ternatea",
"Clubmoss",
"Cnidium monnieri",
"Cocoa Extract",
"Coconut Oil",
"Codonopsis pilosula",
"Coenzyme Q10",
"Coffee",
"Cold Exposure",
"Coleus forskohlii",
"Colostrum",
"Coluracetam",
"Conjugated Linoleic Acid",
"Convolvulus pluricaulis",
"Copper",
"Cordyceps",
"Crataegus pinnatifida",
"Creatine",
"Creatinol O-Phosphate",
"Cucurbita pepo",
"Curcumin",
"Cyanidin",
"D-Aspartic Acid",
"D-Ribose",
"D-Serine",
"DMAE",
"Dactylorhiza hatagirea",
"Damiana Leaf",
"Dark Therapy",
"Dehydroepiandrosterone",
"Dendrobium",
"Diindolylmethane",
"Dimocarpus longan",
"Dioscorea villosa",
"ECA",
"Ecdysteroids",
"Echinacea",
"Ecklonia cava",
"Eclipta alba",
"Egg (Chicken)",
"Eleutherococcus senticosus",
"Emblica officinalis",
"Energy Drinks",
"Ephedrine",
"Eriobotrya japonica",
"Eschscholzia californica",
"Eucommia ulmoides",
"Euonymus alatus",
"Eurycoma Longifolia Jack",
"Evodia rutaecarpa",
"Evolvulus alsinoides",
"Fadogia agrestis",
"Fennel Essential Oil",
"Fenugreek",
"Ferula asafoetida",
"Feverfew",
"Fish Oil",
"Folic Acid",
"Fucoxanthin",
"GABA",
"Gamma Oryzanol",
"Ganoderma lucidum",
"Garcinia cambogia",
"Garlic",
"Ginger",
"Ginkgo biloba",
"Glucosamine",
"Glucuronolactone",
"Glutamine",
"Glutathione",
"Gluten",
"Glycine",
"Grape Seed Extract",
"Grapefruit",
"Green Coffee Extract",
"Green Tea Catechins",
"Griffonia simplicifolia",
"Guggul",
"Gynostemma pentaphyllum",
"HMB",
"Harpagophytum procumbens",
"Hederagenin",
"Hemp Protein",
"Hesperidin",
"Hibiscus macranthus",
"Hibiscus rosasinensis",
"Hibiscus sabdariffa",
"Higenamine",
"Holy Basil",
"Hoodia gordonii",
"Hordenine",
"Horny Goat Weed",
"Horse Chestnut",
"Hovenia dulcis",
"Huperzine-A",
"Hypericum perforatum",
"Idebenone",
"Inositol",
"Iodine",
"Iron",
"Irvingia gabonensis",
"Isoleucine",
"Japanese Knotweed",
"Juniperus chinensis",
"Kaempferia parviflora",
"Kaempferol",
"Kava",
"Ketogenic diet",
"King Oyster",
"Kombucha",
"Krill Oil",
"L-Carnitine",
"L-DOPA",
"L-Threonate",
"L-Tyrosine",
"Lactobacillus casei",
"Lactobacillus reuteri",
"Lavender",
"Leucic Acid",
"Leucine",
"Licorice",
"Light Therapy",
"Limonene",
"Lutein",
"Lysine",
"Maca",
"Magnesium",
"Magnolia officinalis",
"Manganese",
"Mangifera indica",
"Marijuana",
"Massularia acuminata",
"Medium-chain triglycerides",
"Melatonin",
"Melissa officinalis",
"Methylsulfonylmethane",
"Microlactin",
"Milk Protein",
"Milk Thistle",
"Minoxidil",
"MitoQ",
"Modafinil",
"Molybdenum",
"Moringa oleifera",
"Morus alba",
"Mucuna pruriens",
"Muira puama",
"Music",
"Myricetin",
"N-Acetylcysteine",
"Nardostachys jatamansi",
"Nattokinase",
"Nefiracetam",
"Nelumbo nucifera",
"Nicotine",
"Nigella sativa",
"Nitrate",
"Noopept",
"Nutmeg",
"Octopamine",
"Oleamide",
"Oleoylethanolamide",
"Olive Oil",
"Olive leaf extract",
"Ophiopogon japonicus",
"Origanum vulgare",
"Ornithine",
"Orthosiphon stamineus",
"Oxaloacetate",
"Oxiracetam",
"Oxytropis falcate",
"PRL-8-53",
"Paederia foetida",
"Palmatine",
"Panax ginseng",
"Patchouli",
"Paullinia cupana",
"Pedalium murex",
"Pelargonidin",
"Pelargonium sidoides",
"Peppermint",
"Perilla Oil",
"Phellodendron amurense",
"Phenylethylamine",
"Phenylpiracetam",
"Phosphatidylcholine",
"Phosphatidylserine",
"Piceatannol",
"Picrorhiza kurroa",
"Pine Pollen",
"Piracetam",
"Policosanol",
"Polygala tenuifolia",
"Polypodium leucotomos",
"Pomegranate",
"Potassium",
"Pramiracetam",
"Prickly Pear Fruit",
"Psoralea corylifolia",
"Psyllium",
"Pterostilbene",
"Pueraria lobata",
"Pueraria mirifica",
"Punicalagins",
"Punicic Acid",
"Pycnogenol",
"Pygeum",
"Pyritinol",
"Pyrroloquinoline quinone",
"Pyruvate",
"Quercetin",
"Raspberry Ketone",
"Rauwolscine",
"Red Clover Extract",
"Red Yeast Rice",
"Resveratrol",
"Rhaponticum carthamoides",
"Rhodiola Rosea",
"Rooibos",
"Rose Essential Oil",
"Rose Hip",
"Rosmarinic Acid",
"Royal Jelly",
"Rubus coreanus",
"Rubus suavissimus",
"Ruscus aculeatus",
"S-Adenosyl Methionine",
"Safflower Oil",
"Saffron",
"Salacia reticulata",
"Salvia hispanica",
"Salvia miltiorrhiza",
"Salvia sclarea",
"Sarcosine",
"Saw Palmetto",
"Sceletium tortuosum",
"Schisandra chinensis",
"Schizonepeta tenuifolia",
"Scutellaria baicalensis",
"Sea Buckthorn",
"Selenium",
"Senna alexandrina",
"Serrapeptase",
"Sesamin",
"Shilajit",
"Silica",
"Silk Amino Acids",
"Simmondsia chinensis",
"Sodium Bicarbonate",
"Sophora flavescens",
"Soy Isoflavones",
"Soy lecithin",
"Sphaeranthus indicus",
"Spilanthes acmella",
"Spirulina",
"Squalene",
"Stephania tetrandra",
"Stevia",
"Stinging Nettle",
"Sulbutiamine",
"Sulforaphane",
"Sunifiram",
"Synephrine",
"Syzygium aromaticum",
"T3",
"Taraxacum officinale",
"Taurine",
"Tauroursodeoxycholic Acid",
"Tea (Camellia Sinensis)",
"Terminalia arjuna",
"Tetradecyl Thioacetic Acid",
"Theacrine",
"Theaflavins",
"Theanine",
"Tinospora cordifolia",
"Traditional Chinese Medicine",
"Trametes versicolor",
"Trehalose",
"Tribulus terrestris",
"Trichopus zeylanicus",
"Trimethylglycine",
"Tripterygium wilfordii",
"Tulbaghia violacea",
"Turmeric",
"Type-II Collagen",
"Uncaria rhynchophylla",
"Uncaria tomentosa",
"Uridine",
"Ursolic Acid",
"Uva ursi",
"Valeriana officinalis",
"Valine",
"Vanadium",
"Vegan Diet",
"Velvet Antler",
"Vinpocetine",
"Vitamin A",
"Vitamin B1",
"Vitamin B12",
"Vitamin B2",
"Vitamin B3 (Niacin)",
"Vitamin B5",
"Vitamin B6",
"Vitamin C",
"Vitamin D",
"Vitamin E",
"Vitamin K",
"Vitex agnus castus",
"Watercress",
"Whey Protein",
"White Kidney Bean Extract",
"Wine",
"Yacon",
"Yamabushitake",
"Yerba mate",
"Yohimbine",
"ZMA",
"Zeaxanthin",
"Zinc",
"Ziziphus jujuba",
]