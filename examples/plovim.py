# NOTE: While this is definitely ready for use, it should be noted that it does
# *not* play nicely with the asterisk-undo in the English steno system; and that
# it also *won't* play nicely with the suggestions window. To fix both of these,
# all keypresses would have to be marked as, well, keypresses, but I'll only add
# that later.

# NOTE: This whole file is meant to be editable to match what you want from the
# vim system, and I mean that from top to bottom. *Especially* the main sub-
# dictionaries (so `commands_with_motion`, `command_motion_kinds`, `motions`,
# `text_objects`, `with_character`, `characters`, `with_mark`, `marks`,
# `other_commands` and `registers`).

# NOTE: This is generally meant to be used modally (just like vim), for which
# I'd recommend `plover-dict-commands` (it's in the PyPI). You could of course
# change the final dict to have a prefix of another chord, for example; or use
# some other mechanism. `go_into_insert` is appended to anything that would go
# back into insert mode.

import plovary
from plovary import *

import string

from itertools import takewhile

from typing import *

# Make the symbols dictionary importable:
import os, sys
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path: sys.path.append(path)

from symbols import symbols, system as symbol_system


plovary.warn_steno_order = False


go_into_insert = "{PLOVER:END_SOLO_DICT}"


english_system = system
system = EnglishSystem(
    name=f"VIM theory in {EnglishSystem.sys_name}",
    overlay_replacements={
        # I'm using lowercase so that it can't conflict with
        # the english theory
        "i-": ["S-"],  # insert
        "l-": ["T-"],  # list
        "m-": ["K-"],  # modify, macro
        "f-": ["W-"],  # format
        "y-": ["R-"],  # yank
        "p": ["O"],  # pipe
        "b": ["E"],  # beginning
        "e": ["U"],  # end
        "-i": ["-F"],  # incomplete (→ partial)
        "-←": ["-R"],  # down
        "-↓": ["-B"],  # down
        "-f": ["-L"],  # find
        "-↑": ["-G"],  # up
        "-v": ["-T"],  # view
        "-→": ["-S"],  # right
        "-w": ["-D"],  # word
        "-s": ["-Z"],  # smart, spaces
    },
    optional_replacements={
        # my- ⇒ delete, think "destructive (→ modifying) yanking":
        "d-": ["K-", "R-"],
        # mfy- ⇒ cursor:
        "(cursor)-": ["K-", "W-", "R-"],
        # be ⇒ around:
        "a": ["E", "U"],
        # *be ⇒ centre:
        "c": ["*", "E", "U"],
        # -←→ ⇒ line:
        "-l": ["-R", "-S"],
        # -←↓↑→ ⇒ block / file
        "-(block)": ["-R", "-B", "-G", "-S"],
        "-(file)": ["-R", "-B", "-G", "-S"],
        # -←w ⇒ sentence (think -←→w, but actually possible
        # without shifting your fingers)
        "-(sentence)": ["-R", "-D"],
        # *←w ⇒ paragraph
        "-(paragraph)": ["*", "-R", "-D"],
        "-(WORD)": ["-D", "-Z"],
        # -v→ws ⇒ paranthesis like (no real meaning behind this
        # binding though)
        "-(paren)": ["-T", "-S", "-D", "-Z"],
    },
    layout_unused=["P-", "T-", "A", "-P"],
)


T = TypeVar("T")

def convert_system(
    d: Dictionary[Chord[EnglishSystem], T]
) -> Dictionary[Chord[EnglishSystem], T]:
    return Dictionary((system.chord_of_real_keys(k.keys), v) for k, v in d)


insert_commands_with_motion: List[str] = []


def insert_cwm(value: str) -> str:
    insert_commands_with_motion.append(value)
    return value


def insert(number_count: int, value: str) -> Tuple[int, str]:
    return (number_count, value + go_into_insert)


commands_with_motion = system.parsed_single_dict({
    # pipe is generally used to mean something that essentially
    # works with streams of data

    # y- and- i- are used for their shape in `g~`, `gu` and `gU`
    # In my mind, up and right are more related than up and
    # left, hence y- stands for lowercase and i- for uppercase
    "imyp": "g~",  # Switch case, modify the case (streaming)
    "imp": "gu",  # Lowercase, modify the case (streaming)
    "myp": "gU",  # Uppercase, modify the case (streaming)
    "mfp": "g?",  # rot13, modify the format (streaming)
    "fp": "gq",  # formatting (streaming)
    # formatting, but puts the cursor back (streaming):
    "(cursor)p": "gw",
    "p": insert_cwm("!"),  # pipe
    # y- and i- are used for their shape in `=`, `<` and `>`
    # auto indent, modification involving formatting:
    "imfy": "=",
    "imf": "<",  # dedent, modification involving formatting
    "mfy": ">",  # indent, modification involving formatting
    "id": insert_cwm("c"),  # change, delete and insert
    "d": "d",  # delete
    # fold, "appearance formatting", you "yank" the folded part
    # out of your view:
    "fy": "zf",
    "y": "y",  # yank
})

command_motion_kinds = system.parsed_single_dict({
    "*": "v",  # force char wise
    "*l": "V",  # force line wise
    "*(file)": "{#Control_L(v)}",  # force blockwise
})

# the second tuple element always means with how many digits
# this command can be combined in one chord

# Combine with the commands above
motions = system.parsed_single_dict({
    "-←": (1, "h"),  # left
    "-↓": (1, "j"),  # down
    "-↑": (1, "k"),  # up
    "-→": (1, "l"),  # right

    "-l↓v": (1, "gj"),  # character visually below
    "-l↑v": (1, "gk"),  # character visually above

    "bl": (0, "0"),  # line start
    "bls": (0, "^"),  # "smart" because it skips whitespace
    "cl": (0, "gM"),  # line middle
    "cls": (0, "gM"),
    "el": (0, "$"),  # line end
    "els": (0, "$"),

    "blv": (0, "g0"),  # visual line start
    "blvs": (0, "g^"),
    "clv": (0, "gm"),
    "clvs": (0, "gm"),
    "elv": (0, "g$"),
    "elvs": (0, "g$"),

    "-l": (1, "gM"),  # go to percentage of line

    "-l↓s": (1, "+"),  # go lines up and to first non-blank
    "-l↑s": (1, "-"),  # go lines down and to first non-blank

    "b(file)": (0, "gg"),  # first line of the file
    "e(file)": (0, "G"),  # last line of the file
    # last character of file:
    "*e(file)": (0, "{#Control_L(End)}"),

    "-(file)": (1, "G"),  # go to line in file

    "bv": (0, "H"),  # go to the first line in the view
    "cv": (0, "M"),  # go to the middle line in the view
    "ev": (0, "L"),  # go to the last line in the view

    "b↓w": (1, "b"),  # previous word beginning
    "bw": (1, "b"),
    "b↑w": (1, "w"),  # next word beginning
    "e↓w": (1, "ge"),  # previous word end
    "e↑w": (1, "e"),  # next word end
    "ew": (1, "e"),

    "b↓(WORD)": (1, "B"),  # previous WORD beginning
    "b(WORD)": (1, "B"),
    "b↑(WORD)": (1, "W"),  # next WORD beginning
    "e↓(WORD)": (1, "gE"),  # previous WORD end
    "e↑(WORD)": (1, "E"),  # next word end
    "e(WORD)": (1, "E"),
    # The stuff above nine times without shifting fingers:
    "b↓9S(WORD)": (1, "9B"),
    "b9S(WORD)": (1, "9B"),
    "b↑9S(WORD)": (1, "9W"),
    "e↓9S(WORD)": (1, "9gE"),
    "e↑9S(WORD)": (1, "9E"),
    "e9S(WORD)": (1, "9E"),

    "b(sentence)↓": (1, "("),  # previous sentence beginning
    "-(sentence)↓": (1, "("),
    "b(sentence)↑": (1, ")"), # next sentence beginning
    "-(sentence)↑": (1, ")"),
    "b(sentence)": (1, ")"),

    "b(paragraph)↓": (1, "\\{"),  # previous paragraph beginning
    "-(paragraph)↓": (1, "\\{"),
    "b(paragraph)↑": (1, "}"),  # next paragraph beginning
    "-(paragraph)↑": (1, "}"),
    "b(paragraph)": (1, "}"),

    # See the text objects for them
    "b(paren)": (1, "[("),  # go to unmatched ( before
    "e(paren)": (1, "])"),  # go to unmatched ( after
    "bF(paren)": (1, "[\\{"),  # go to unmatched { before
    "bF(paren)": (1, "]}"),  # go to unmatched { after
    "-b↓fs": (1, "[m"),  # (find and) go to previous method beginning
    "-bf↑s": (1, "[m"),  # go to next method beginning
    "-ef↑s": (1, "[m"),  # go to next method end
    "*b↓fs": (1, "[*"),  # go to previous multiline comment start
    "*bf↑s": (1, "[*"),  # go to next multiline comment start
    # go to previous unmatched `#if` or `#else` (think of the preprocessor as
    # less smart; though the `-s` is only missing for disambiguation)
    "-b↓f": (1, "[#"),
    "-bf↑": (1, "]#"),  # go to next unmatched `#else` of `#endif`

    "-lf": (1, ";"),  # repeat last `f`, `F`, `t` or `T`
    "*lf": (1, ","),  # repeat it in the opposite direction

    "-s": (0, "%"),  # go to matching parenlike
})

text_objects = (
    system.toggle("a", "a", default="i") *
    system.parsed_single_dict({
        "-w": "w",  # word
        "-(WORD)": "W",  # WORD
        "-(sentence)": "s",  # sentence
        "-(paragraph)": "p",  # paragraph

        "-(paren)": "(",  # ()

        # The extra keys for parenlikes do not have any real
        # meaning, but the further left they are the less pointy
        # and more swirly they get
        "-F(paren)": "\\{",  # {}
        "-P(paren)": "[",  # []
        "-L(paren)": "<",  # <>

        # tags (← and →, in ASCII < and >, are both pressed here):
        "-←(paren)": "t",

        "-FR(paren)": "`",  # points to the top left
        "-LG(paren)": "'",  # points to the top right in comparison
        "-FRLG(paren)": "\"",  # both together
    })
)

# These cannot take numbers directly
with_character = system.parsed_single_dict({
    "-l↓f": "F",  # find character in line before cursor
    "-lf↑": "f",  # find character in line after cursor
    # find character in line before cursor but stop one before:
    "-il↓f": "T",
    # find character in line after cursor but stop one before:
    "-ilf↑": "t",
})

characters = (
    convert_system(fingertyping) +
    convert_system(symbols)
        .map(keys=sub(system.chord(*symbol_system.always_pressed)))
)

# These cannot take numbers
with_mark = system.parsed_single_dict({
    "(cursor)*": "m",  # create mark
    "(cursor)": "'",  # jump to mark
    "l(cursor)*": "g'",  # jump to mark without changing the jump list
})

marks = system.parsed_single_dict({
    # local
    "-FR": "a",
    "-PB": "b",
    # global
    "-LG": "A",
    "-TS": "B",
    # previously yanked or changed
    "bTD": "[",
    "eTD": "]",
    # previously selected
    "bSZ": "<",
    "eSZ": ">",
})

other_commands = system.parsed_single_dict({
    "*l": (1, "|"),  # go to screen column

    "*(file)": (1, "%"),  # go to percentage of file
    # go to byte in file, the `s` is only for disambiguation:
    "-(file)s": (1, "go"),
    "*(file)s": (1, "go"),

    "l(cursor)-↓": (0, "{#Control_L(o)}"),  # go back in the jump list
    "l(cursor)-↑": (0, "{#Control_L(i)}"),  # go forth in the jump list
    "l(cursor)": (0, ":ju{#Return}"),  # show jump list

    "lm-↓": (0, "g;"),  # go back in change list
    "lm*↑": (1, "2g;"),  # go back in change list twice
    "lm-↑": (0, "g,"),  # go forth in change list
    "lm": (0, ":changes{#Return}"),  # show change list

    # add the given amount to the number under the cursor (modify something
    # formatted as a number by increasing it), defaults to one
    "mf-↑": (1, "{#Control_L(a)}"),  
    "mf-↓": (1, "{#Control_L(x)}"),  # decrease the amount, defaults to one

    "-↑v": (1, "{#Control_L(b)}"),  # scroll screen up
    "-↓v": (1, "{#Control_L(f)}"),  # scroll screen down

    "-←↓→": (1, "{#Control_L(d)}"),  # scroll lines down
    # scroll half screen down
    "c↓v": (0, ":set scroll=0{#Return}{#Control_L(d)}"),

    "i": insert(0, "i"),  # go into insert mode before cursor
    "ib": insert(0, "i"),
    "i*": insert(0, "a"),  # go into insert mode after cursor
    "ie": insert(0, "a"),

    "m": insert(0, ":"),  # enter ex command

    "m-↓": (1, "u"),  # undo
    "m-↑": (1, "{#Control_L(r)}"),  # redo
})

registers = (
    # named registers:
    system.parsed_single_dict({
        "-FR": "a",
        "-PB": "b",
        "-LG": "c",
        "-TS": "d",
    }).combinations(
        system.toggle("*", True, default=False),
        values=lambda v, add_to_reg: v.upper() if add_to_reg else v
    ) +
    # special registers except the default one and the removal ones:
    system.parsed_single_dict({
        "yAOEU": "0",  # most recent yank
        "iy": ".",  # last inserted
        # For the GUI:
        "y-FPLTD": "*",
        "y-RBGSZ": "+",
    }) +
    # most recent removals:
    (convert_system(single_digit_only) - [system.chord("0")]).map(keys=add("y"))
).map(values=prefix("\""))

def add_numbered_versions(
    d: Dictionary[Chord[EnglishSystem], Tuple[int, str]],
    *,
    keep_one: bool,
) -> Dictionary[Chord[EnglishSystem], str]:
    def fix_overlaps(
        main_key: Chord[EnglishSystem],
        numbers: Dictionary[Chord[EnglishSystem], T]
    ) -> Dictionary[Chord[EnglishSystem], T]:
        return Dictionary(takewhile(lambda x: not x[0].overlaps(main_key), numbers))

    return Dictionary(
        (k + k2, number.lstrip("0") + v)
        for k, (max_digit_count, v) in d
        for digit_count in range(max_digit_count + 1)  # inclusive range
        for k2, number in {
            0: Dictionary([(system.empty_chord, "")]),
            1: fix_overlaps(
                k,
                (
                    convert_system(single_digit_only) - [system.chord("1-")]
                    if not keep_one else
                    convert_system(single_digit_only)
                ) - [system.chord("0")]
            ),
        }[digit_count]
    )

combining_right = (
    add_numbered_versions(motions, keep_one=False) +
    text_objects
)

combined = commands_with_motion * combining_right

def add_into_insert(value: str) -> str:
    if any(value.startswith(i) for i in insert_commands_with_motion):
        return value + go_into_insert
    else:
        return value

final_dict = (
    (commands_with_motion * combining_right).map(values=add_into_insert) +
    commands_with_motion * command_motion_kinds.with_empty_chord() +
    add_numbered_versions(motions, keep_one=True) +
    text_objects +
    with_character * characters +
    with_mark * marks +
    add_numbered_versions(other_commands, keep_one=True) +
    registers +
    convert_system(numbers)
).map(values=surround("{^}", "{^}"))

final_dict.plover_dict_main(__name__, globals())
