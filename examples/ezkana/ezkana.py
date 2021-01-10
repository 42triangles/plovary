from typing import *
from plovary import *

suffix = chord("-LGDZ")
# only isn't needed here, but this way `mypy` checks that this
# is really just a single correct key:
add_y = chord(only="-F")
submit = chord(only="-R")
add_tu = chord(only="-P")
add_n = chord(only="-B")

# Everything is done in combinations of two
# * Space for a consonant means no consonant
# * "l" as a consonant means small y+vowel if it exists,
#   otherwise it's a small vowel
# * "xu" is a small "tu"
# * "nn" is an n without a vowel
# * "--" is the katakana elongation thingy

small_tu = dictionary({
    to_dict_key(add_tu): "xu",
})

n = dictionary({
    to_dict_key(add_n): "nn",
})

# This is only available in Katakana mode, so the asterisk is
# there, even in IME mode (where Katakana mode only consists of
# this, because I have yet to figure out how to give `ibus`
# katakana explicitly)
katakana_elongate = dictionary({
    to_dict_key("AOEU"): "--",
})

normal_consonants = dictionary(
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

no_consonant = dictionary({to_dict_key(Chord.empty()): " "})

y_consonants = normal_consonants.map(
    keys=combine_first_chord(add_y),
    values=lambda x: x + "il",
)

special_consonants = dictionary({
    to_dict_key("SH"): "si",  # sh
    "KH": "ti",  # ch
    "TP": "hu",  # f
    "SKWR": "zi",  # j
})

vowels = dictionary(
    (fingertyping_lowercase_no_asterisk.keys_for(k)[0], k)
    for k in ["a", "i", "u", "e", "o"]
) + dictionary({
    to_dict_key("AE"): "a a",
    "AOE": "i i",
    "AOU": "u u",
    "AEU": "e i",
    "OU": "o u",
})

simple_consonants = (
    normal_consonants + no_consonant + y_consonants
)

simple_combinations = simple_consonants.cross_product(
    vowels,
    keys=combine_single_chords,
)

special_combinations = special_consonants.cross_product(
    vowels,
    keys=combine_single_chords,
    values=lambda cv, v: (
        cv + v[1:]
        if cv.endswith(v[0])
        else cv + "l" + v
    ),
)

combinations = simple_combinations + special_combinations

extended_combinations = (
    (
        small_tu + dictionary({to_dict_key(Chord.empty()): ""})
    ).cross_product(
        combinations,
        keys=combine_single_chords,
    ) + small_tu
).cross_product(
    n + dictionary({to_dict_key(Chord.empty()): ""}),
    keys=combine_single_chords,
) + n

katakana_combinations = (
    extended_combinations + katakana_elongate
)

def translate(
    dictionary: Dictionary,
    symbol_mapping: Callable[[str], str]
) -> Dictionary:
    def value_mapping(output: str) -> str:
        assert len(output) % 2 == 0

        return "".join(
            symbol_mapping(output[i:i+2])
            for i in range(0, len(output), 2)
        )

    return dictionary.map(values=value_mapping)

def handle_ime() -> Dictionary:
    def translate_symbol(symbol: str) -> str:
        symbol = (
            "ltu"
            if symbol == "xu"
            else (
                "-"
                if symbol == "--"
                else symbol.replace(" ", "")
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
        extended_combinations +
            katakana_elongate.with_asterisk(),
        translate_symbol,
    ).cross_product(
        dictionary({
            to_dict_key(submit): "a{^}{#Backspace}{^ ^}",
            Chord.empty(): "",
        }),
        keys=combine_single_chords,
    )

def handle_proper() -> Dictionary:
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
        translate(
            extended_combinations,
            translation_for(hiragana),
        ) +
        translate(
            extended_combinations + katakana_elongate,
            translation_for(katakana),
        ).with_asterisk()
    ).cross_product(
        dictionary({
            to_dict_key(submit): "",
            Chord.empty(): "",
        }),
        keys=combine_single_chords,
    )

def finalize(dictionary: Dictionary) -> Dictionary:
    return dictionary.map(
        keys=combine_first_chord(suffix),
        values=lambda x: "{^}" + x + "{^}",
    )

final_ime = finalize(handle_ime())
final_proper = finalize(handle_proper())
