# local_knowledge.py

local_facts = {
    "hymne": {
        "francais": """
L'Hymne National, LE DITANYE

Contre la férule humiliante il y a déjà mille ans,
La rapacité venue de loin les asservir il y a cent ans.
Contre la cynique malice métamorphosée
En néocolonialisme et ses petits servants locaux
Beaucoup flanchèrent et certains résistèrent.
Mais les échecs, les succès, la sueur, le sang
Ont fortifié notre peuple courageux
Et fertilisé sa lutte héroïque.

REFRAIN :
Et une seule nuit a rassemblé en elle
L'histoire de tout un peuple.
Et une seule nuit a déclenché sa marche triomphale :
Vers l'horizon du bonheur.
Une seule nuit a réconcilié notre peuple
Avec tous les peuples du monde,
À la conquête de la liberté et du progrès
La Patrie ou la mort, nous vaincrons !
""",
        "moore": """
Burkĩmba pĩnd n kisga wõrbo la yãnde hal yʋʋm tusri
B kisga fãadbã sẽn yi yɩɩga hal yʋʋm koabga n wa nĩ yembdo
B tõdga sɩlem wɛɛgã sẽn toeem n lebg yaolem yembdo
B kisga sɩlem wɛɛgã yembdo nĩ a tẽng n tɛɛndbã fãa gilli
Wʋsg n bas raoodo la kẽer mẽ sɩd zãagsam
La pãng kongrã la tõogrã la tʋʋlgã kãagre
Zɩɩmã raagre kenga nimbuiidã pelse
La b paasa b pãng n leb n zẽk b burkĩndi

REESGO :
La yʋnga ye tãa a ye tãa kʋmba nimbuiidã vɩɩm kibare
La yʋnga ye tãa bal pʋgẽ waa tilgre sor pakam tɩ b rɩk n babsd vɩ-nõogo
Yʋnga ye lagma tõnd nimbuiidã
Nĩ nimbuiidã sẽn be dũni wã fãa pʋgẽ
N baood tilgre la paoongo nẽ b sũurã fãa
Kal tɩ d tõoge ba d na n ki d tẽng yĩnga.
""",
        "dioula": """
Faso Fasa
Sebagaya Faso
Saan baa kelen,
golokami n'a maloya
kosɔn

Ani saan kɛmɛ
Ninjuguya ni 
Jɔnyajugu Kosɔn
Faso fasa
Kɔnɔnajuguya fana,
kosɔn, O bayɛlɛmanin
koloniyalisimukura la
N'a batobagajuguw
Caaman segira kɔ, nga dɔɔw lɔra kelen kan
Nga dɛsɛ, hɛɛrɛ, wɔsiji
ni joli
O le y'an ka Faso jama
Fariya 
K'a ka cɛfariya kɛlɛ lasinsin

Suu kelen pewu y'an
 ka jamana tariku lajɛn
a yɛrɛ ye
Suu kelen pewu y'an
  Ka masayataama
latigɛ
Daamu ɲinisira kan, o
Suu kelen kɛra sababu
Ye
K'an ka jama ni diɲɛ
Jama bɛɛ kaan bɛn
hɔɔrɔnya ni ɲɛtaga ɲini 
na u yɛrɛ ye
Faso walima saya, see y'an taa ye
"""
    },
    "president": "Le président du Burkina Faso est Ibrahim Traoré.",
    "salutations": {
        "moore": {
            "bonjour": ["Yibéogo !", "Ney Yibéogo !"],
            "comment ça va": "Kibaré ?",
            "ça va": "Laafi",
            "ça va bien": "Laafi bala",
            "merci": "Barka",
            "merci beaucoup": "Barka wousgo",
            "au revoir": "Bilfou",
            "bonne journée": "Yom wi a yibeoogo",
            "matin": "A ni sɔ̀gɔma",
            "midi": "A ni tlé",
            "apres-midi": "A nou laa",
            "soir": "A ni zaabre",
            "nuit": "I nou su"
        },
        "dioula": {
            "bonjour": "Inché",
            "matin": "One baali diiam",
            "entre 11h-13h": "One beeti diiam",
            "apres-midi": "One nyaali diiam",
            "soir": "One keeri diiam",
            "comment ça va": ["Djam na ?", "A djamo na ?"],
            "ça va": "Djam tan",
            "ça va bien": "Djam doron tan",
            "as-tu bien dormi": "A waali djam na ?",
            "merci": "I ni tché",
            "au revoir": "Kan bèn"
        },
        "fulfulde": {
            "bonjour": ["Jam wali", "On jaraama"],
            "comment ça va": "No mbadda ?",
            "ça va": "Jam tan",
            "ça va bien": "Jam e jam",
            "merci": "Jaaraama",
            "merci beaucoup": "Jaaraama buri",
            "au revoir": "Fof ma yaaf on",
            "bonne journée": "Ñalnde e jam",
            "matin": "Fii subaka",
            "soir": "Fii hiirde",
            "nuit": "Jamma"
        },
        "francais": {
            "bonjour": "Bonjour",
            "bonsoir": "Bonsoir",
            "merci": "Merci",
            "au revoir": "Au revoir",
            "bonne journée": "Bonne journée"
        }
    },

    "numeros_utiles": {
        "orange": {
            "service_client": "121",
            "description": "Service client Orange, disponible 7 jours sur 7, 24 heures sur 24"
        },
        "orange_money": {
            "service_client": "127",
            "menu_ussd": "*144#",
            "solde": "*144*9*1#",
            "description": "Service client Orange Money, disponible 7 jours sur 7, 24 heures sur 24"
        },
        "orange_energie": {
            "service_client": "119",
            "menu_ussd": "*244#",
            "paiement": "*244*1*1*1#",
            "description": "Service Orange Energie, installation sous 72 heures après validation"
        },
        "codes_ussd": {
            "solde": "*160#",
            "recharge": "*123*code#",
            "transfert_credit": "*111#",
            "numero_orange": "*100#"
        },
        "contact_additionnel": "+226 07 00 01 21",
        "email": "info.obf@orange.com"
    },
    "accueil_autorites": "Souhaitez la bienvenue aux autorités présentes avec respect et courtoisie."
}

def get_fact(query):
    """Retourne la réponse locale si le query correspond à un mot-clé connu."""
    q = query.lower()
    if "hymne" in q:
        return local_facts["hymne"]
    elif "président" in q or "president" in q:
        return local_facts["president"]
    elif "salut" in q or "bonjour" in q or "comment ça va" in q or "au revoir" in q:
        return local_facts["salutations"]
    elif "autorité" in q or "bienvenue" in q:
        return local_facts["accueil_autorites"]
    return None
