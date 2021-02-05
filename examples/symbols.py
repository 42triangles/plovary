from plovary import *

system = EnglishSystem(
    name=f"Symbols in {EnglishSystem.sys_name}",
    optional_replacements={},
    overlay_replacements={
        "2-": ["S-"],
        "↖-": ["T-"],
        "↙-": ["K-"],
        "↗-": ["P-"],
        "↘-": ["W-"],
        "↑-": ["H-"],
        "↓-": ["R-"],
        "←": ["A"],
        "—": ["O"],
        "◯": ["E"],
        "→": ["U"],
        "-⇢": ["-T"],
        "-⇠": ["-D"],
        "()-": ["T-", "K-"],
        "~-": ["P-", "W-"],
    },
    layout_unused=["#", "-P", "-B", "-S", "-Z"],
    always_pressed=["-F", "-R", "-L", "-G"],
    parse_mandatory_replacements=False,
)

symbols = system.parsed_single_dict({
    "2↖↙↗↘—": "#",
    "2↑↓◯": ":",
    "S↑↓": "$",
    "2↑—": '"',
    "2—◯": "&",
    "2—": "=",
    "2↑↓—": "=",
    "S◯": "?",
    "↖↙↗↘—": "*",
    "()~←": "\\{",
    "()~→": "\\}",
    "()←—": "[",
    "()—→": "]",
    "()←◯": "(",
    "()◯→": ")",
    "↖↘—": "\\ ",
    "↖↑—": "`",
    "↙↗—◯": "%",
    "↙↗—": "/",
    "↙↘↑—": "^",
    "↑": "^",
    "↙↓—": ",",
    "↙↑↓—◯": ";",
    "~": "~",
    "↑↓—": "|",
    "↑↓—◯": "!",
    "↑↓←—→": "+",
    "↑—": "'",
    "↓—": "_",
    "A◯": "@",
    "←": "<",
    "→": ">",
    "—": "-",
    "◯": ".",
})

final_dict = (
    system.toggle("-⇠", "{^}") *
    symbols *
    system.toggle("-⇢", "{^}")
)

final_dict.plover_dict_main(__name__, globals())
