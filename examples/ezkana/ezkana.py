from typing import *
from plovary import *
import os

# "English Single Chord DICTionary"
ESCDict = Dictionary[Chord[EnglishSystem], str]

shared = system.parse("-LGDZ")
# only isn't needed here, but this way `mypy` checks that this
# is really just a single correct key:
add_y = system.chord("-F")
submit = system.chord("-R")
add_tu = system.chord("-P")
add_n = system.chord("-B")

# Everything is done in combinations of two
# * Space for a consonant means no consonant
# * "l" as a consonant means small y+vowel if it exists,
#   otherwise it's a small vowel
# * "xu" is a small "tu"
# * "nn" is an n without a vowel
# * "--" is the katakana elongation thingy

small_tu = Dictionary({add_tu: "xu"})

n = Dictionary({add_n: "nn"})

# This is only available in Katakana mode, so the asterisk is
# there, even in IME mode (where Katakana mode only consists of
# this, because I have yet to figure out how to give `ibus`
# katakana explicitly)
katakana_elongate = system.parsed_single_dict({"AOEU": "--"})

normal_consonants = Dictionary(
    (fingertyping_lowercase_no_asterisk.keys_for(k)[0], k)
    for k in [
        "k", "g",
        "s", "z",
        "t", "d",
        "n",
        "h", "b", "p",
        "m",
        "y",
        "r",
        "w",
        "l"
    ]
)

no_consonant = Dictionary({system.empty_chord: " "})

y_consonants = normal_consonants.map(keys=add(add_y), values=suffix("il"))

special_consonants = system.parsed_single_dict({
    "SH": "si",  # sh
    "KH": "ti",  # ch
    "TP": "hu",  # f
    "SKWR": "zi",  # j
})

vowels = Dictionary(
    (fingertyping_lowercase_no_asterisk.keys_for(k)[0], k)
    for k in ["a", "i", "u", "e", "o"]
) + system.parsed_single_dict({
    "AE": "a a",
    "AOE": "i i",
    "AOU": "u u",
    "AEU": "e i",
    "OU": "o u",
})

simple_consonants = normal_consonants + no_consonant + y_consonants

simple_combinations = simple_consonants * vowels

special_combinations = special_consonants.combinations(
    vowels,
    values=lambda cv, v: (
        cv + v[1:]
        if cv.endswith(v[0])
        else cv + "l" + v
    ),
)

combinations = simple_combinations + special_combinations

extended_combinations = (
    (small_tu.with_empty_chord() * combinations + small_tu) *
    n.with_empty_chord() +
    n
)

katakana_combinations = extended_combinations + katakana_elongate

def translate(
    dictionary: ESCDict,
    symbol_mapping: Callable[[str], str]
) -> ESCDict:
    def value_mapping(output: str) -> str:
        assert len(output) % 2 == 0

        return "".join(
            symbol_mapping(output[i:i+2])
            for i in range(0, len(output), 2)
        )

    return dictionary.map(values=value_mapping)

def handle_ime() -> ESCDict:
    def translate_symbol(symbol: str) -> str:
        symbol = (
            "ltu"
            if symbol == "xu"
            else (
                "-"
                if symbol == "--"
                else (
                    "ly" + symbol[1]
                    if symbol in ["la", "lu", "lo"]
                    else symbol.replace(" ", "")
                )
            )
        )

        if len(symbol) == 1:
            return symbol
        else:
            return (
                symbol[0] +
                "{^}{#" + " ".join(symbol[1:]) + "}{^}"
            )

    # We don't put anything on the asterisk except the
    # elongating thingy for katakana
    return translate(
        extended_combinations + katakana_elongate.map(keys=add("*")),
        translate_symbol,
    ) * system.toggle(submit, "a{^}{#Backspace}{^ ^}")

def handle_proper() -> ESCDict:
    vowel_order = {
        "a": 0,
        "i": 1,
        "u": 2,
        "e": 3,
        "o": 4,
    }

    hiragana = {
        " ": "あいうえお",
        "k": "かきくけこ",
        "g": "がぎぐげご",
        "s": "さしすせそ",
        "z": "ざじずぜぞ",
        "t": "たちつてと",
        "d": "だぢづでど",
        "n": "なにぬねの",
        "h": "はひふへほ",
        "b": "ばびぶべぼ",
        "p": "ぱぴぷぺぽ",
        "m": "まみむめも",
        "y": "や ゆ よ",
        "r": "らりるれろ",
        "w": "わゐ ゑを",
        "l": "ゃぃゅぇょ",
        "nn": "ん",
        "xu": "っ",
    }

    katakana = {
        " ": "アイウエオ",
        "k": "カキクケコ",
        "g": "ガギグゲゴ",
        "s": "サシスセソ",
        "z": "ザジズゼゾ",
        "t": "タチツテト",
        "d": "ダヂヅデド",
        "n": "ナニヌネノ",
        "h": "ハヒフヘホ",
        "b": "バビブベボ",
        "p": "パピプペポ",
        "m": "マミムメモ",
        "y": "ヤ ユ ヨ",
        "r": "ラリルレロ",
        "w": "ワヰ ヱヲ",
        "l": "ャィュェョ",
        "nn": "ン",
        "xu": "ッ",
    }

    def translation_for(
        table: Dict[str, str]
    ) -> Callable[[str], str]:
        def translate_symbol(symbol: str) -> str:
            if symbol == "--":
                return "ー"
            elif symbol in table:
                return table[symbol]
            else:
                return table[symbol[0]][vowel_order[symbol[1]]]

        return translate_symbol

    return (
        translate(extended_combinations, translation_for(hiragana)) +
        translate(
            extended_combinations + katakana_elongate,
            translation_for(katakana),
        ).map(keys=add("*"))
    ) * system.toggle(submit, "")  # Make submit do nothing here

def finalize(dictionary: ESCDict) -> ESCDict:
    return dictionary.map(
        keys=add(shared),
        values=lambda x: "{^}" + x + "{^}",
    )

final_ime = finalize(handle_ime())
final_proper = finalize(handle_proper())

if __name__ == "__main__":
    if "EZKANA_MODE" in os.environ:
        dictionary = {
            "ime": final_ime,
            "proper": final_proper,
        }[os.environ["EZKANA_MODE"].lower()]
        dictionary.plover_dict_main(__name__, globals())
