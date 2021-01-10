import os, sys
path = os.environ["HOME"] + '/.local/share/plover'
if path not in sys.path: sys.path.append(path)

from plovary import *

symbols = dictionary({
    to_dict_key("STKPWO"): "#",
    "SHRE": ":",
    "SHR-": "$",
    "SHO": '\\"',
    "SOE": "&",
    "SO": "=",
    "SHRO": "=",
    "SE": "?",
    "TKPWO": "*",
    "TKPWA": "\\\\{",
    "TKPWU": "\\\\}",
    "TKAO": "[",
    "TKOU": "]",
    "TKAE": "(",
    "TKEU": ")",
    "TWO": "\\\\ ",
    "THO": "`",
    "KPOE": "%",
    "KPO": "/",
    "KPHO": "^",
    "H-": "^",
    "KRO": ",",
    "KHROE": ";",
    "PW-": "~",
    "HRO": "|",
    "HROE": "!",
    "HRAOU": "+",
    "HO": "'",
    "RO": "_",
    "AE": "@",
    "A": "<",
    "U": ">",
    "O": "-",
    "E": ".",
})

final_dict = dictionary({
    to_dict_key("-D"): "{^}",
    Chord.empty(): "",
}).cross_product(
    symbols,
    keys=combine_single_chords,
).cross_product(
    dictionary({to_dict_key("-T"): "{^}", Chord.empty(): ""}),
    keys=combine_single_chords,
).map(keys=combine_first_chord("-FRLG"))

final_dict.plover_dict_main(__name__, globals())
