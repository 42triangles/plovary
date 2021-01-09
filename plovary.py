from typing import *
from enum import Enum


Key = Literal[
    "#",
    "S", "T", "K", "P", "W", "H", "R",
    "A", "O", "*", "E", "U",
    "-F", "-R", "-P", "-B", "-L", "-G", "-T", "-S", "-D", "-Z",
]

number_bar: Final[Key] = "#"
asterisk: Final[Key] = "*"

left_keys: Final[List[Key]] = ["S", "T", "K", "P", "W", "H", "R"]
left_middle_keys: Final[List[Key]] = ["A", "O", "*"]
right_middle_keys: Final[List[Key]] = ["E", "U"]
middle_keys: Final[List[Key]] = left_middle_keys + right_middle_keys
right_keys: Final[List[Key]] = [
    "-F", "-R", "-P", "-B", "-L", "-G", "-T", "-S", "-D", "-Z"
]
key_order: Final[List[Key]] = (
    [number_bar] + left_keys + middle_keys + right_keys
)
assert set(key_order) == set(get_args(Key)) # Should be the exact same keys
assert len(key_order) == len(set(key_order))  # No duplicates

all_keys: Final[List[Key]] = key_order # This is just an alias

Digit = Literal["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

digit_keys: Final[Dict[Digit, Key]] = {
    "1": "S",
    "2": "T",
    "3": "P",
    "4": "H",
    "5": "A",
    "0": "O",
    "6": "-F",
    "7": "-P",
    "8": "-L",
    "9": "-T",
}
# Should be the same digits:
assert set(digit_keys.keys()) == set(get_args(Digit))

def in_order(a: Union[Key, Digit], b: Union[Key, Digit]) -> bool:
    def to_index(x: Union[Key, Digit]) -> int:
        as_key = digit_keys[cast(Digit, x)] if x in digit_keys else cast(Key, x)
        return key_order.index(as_key)

    return to_index(a) < to_index(b)

def to_key(x: Any) -> Union[Key, Digit]:
    out = str(x)
    if out not in all_keys and out not in digit_keys:
        raise ValueError(f"{x!r} is not a key (or digit)")
    return cast(Union[Key, Digit], out)

reverse_digit_keys: Final[Dict[Key, Digit]] = {
    v: k
    for k, v in digit_keys.items()
}
# Should not leave out anything (because of duplicates):
assert len(digit_keys) == len(reverse_digit_keys)


key_representations: Final[Dict[Key, List[str]]] = {
    i: [i[-1]] + ([reverse_digit_keys[i]] if i in reverse_digit_keys else [])
    for i in all_keys
}


ChordCls = TypeVar('ChordCls', bound='Chord')

class Chord(object):
    keys: Final[FrozenSet[Key]]

    def __init__(self, keys: FrozenSet[Key]) -> None:
        self.keys = keys

    @classmethod
    def parse(cls: Type[ChordCls], chord: str) -> ChordCls:
        if not chord:
            raise ValueError(f"The chord {chord!r} is empty")

        left: List[str] = list(chord)
        out: Set[Key] = set()

        def try_consume(key: Key) -> None:
            if left and left[0] in key_representations[key]:
                del left[0]
                out.add(key)

        for i in left_keys + left_middle_keys:
            try_consume(i)

        if left and left[0] == "-":
            del left[0]

        for i in right_middle_keys + right_keys:
            try_consume(i)

        if set(chord) & set(digit_keys.keys()):
            out.add("#")

        hyphen_maybe_missing = (
            "-" not in chord and  # there is no hyphen
            not out & set(middle_keys) and  # there are no middle keys
            out & set(right_keys)  # but there *are* right keys
        )

        everything_parsed = len(left) == 0

        if hyphen_maybe_missing or not everything_parsed:
            info = (
                " (it may be missing a hyphen)" if hyphen_maybe_missing else ""
            )
            raise ValueError(f"The chord {chord!r} is not valid{info}")

        return cls(frozenset(out))

    @classmethod
    def digit(cls: Type[ChordCls], value: int) -> ChordCls:
        if not (0 <= value < 10):
            raise ValueError(f"{value} is not a single digit")

        return chord("#", digit_keys[cast(Digit, str(value))], ty=cls)

    @classmethod
    def empty(cls: Type[ChordCls]) -> ChordCls:
        return cls(frozenset())

    def _subset(self, *, by: Collection[Key]) -> FrozenSet[Key]:
        return frozenset(i for i in self.keys if i in by)

    @property
    def left_keys(self) -> FrozenSet[Key]:
        return self._subset(by=left_keys)

    @property
    def left_middle_keys(self) -> FrozenSet[Key]:
        return self._subset(by=left_middle_keys)

    @property
    def right_middle_keys(self) -> FrozenSet[Key]:
        return self._subset(by=right_middle_keys)

    @property
    def middle_keys(self) -> FrozenSet[Key]:
        return self._subset(by=middle_keys)

    @property
    def right_keys(self) -> FrozenSet[Key]:
        return self._subset(by=right_keys)

    def _to_str(self, move: Mapping[Key, str]={}) -> str:
        used_move: bool = False

        def do_move(key: Key) -> str:
            used_move = True
            return move[key]

        def part_to_str(part: List[Key]) -> str:
            return "".join(
                do_move(i) if i in move else i[-1]
                for i in part
                if i in self
            )

        out = (
            part_to_str(left_keys + middle_keys) +
            ("-" if self.right_keys and not self.middle_keys else "") +
            part_to_str(right_keys)
        )

        return ("#" if "#" in self and not used_move else "") + out

    def overlaps(self, other: 'Chord') -> bool:
        return bool(self.keys & other.keys)

    def overlaps_besides_special(self, other: 'Chord') -> bool:
        return bool(self.keys & other.keys - frozenset((number_bar, asterisk)))
    
    def combine_nonoverlapping(self, other: 'Chord') -> 'Chord':
        if self.overlaps(other):
            raise ValueError(f"{self} and {other} overlap")
        return self.combine_overlapping(other)

    def combine_overlapping(self, other: 'Chord') -> 'Chord':
        return Chord(self.keys | other.keys)

    def remove_or_ignore(self, other: 'Chord') -> 'Chord':
        return Chord(self.keys - other.keys)

    @property
    def plover_str(self) -> str:
        return self._to_str(reverse_digit_keys)

    def __repr__(self) -> str:
        return f"Chord({self.keys!r})"

    def __str__(self) -> str:
        return self._to_str()

    def __contains__(self, item: Union[Key, Digit, 'Chord']) -> bool:
        if isinstance(item, Chord):
            return item.keys <= self.keys
        elif item in digit_keys:
            return chord(only=item) in self
        else:
            return cast(Key, item) in self.keys

    def __add__(self, other: Union[Key, Digit, 'Chord']) -> 'Chord':
        """
        This does check that the two chords do not overlap, except for the
        number bar and asterisk.
        """
        if isinstance(other, Chord):
            if self.overlaps_besides_special(other):
                raise ValueError(f"{self} and {other} overlap")
            return self.combine_overlapping(other)
        elif other in digit_keys:
            return self + chord(only=other)
        elif other in all_keys:
            return self + Chord(frozenset((cast(Key, other),)))
        else:
            return NotImplemented

    def __radd__(self, other: Union[Key, Digit, 'Chord']) -> 'Chord':
        return self + other

    def __sub__(self, other: Union[Key, Digit, 'Chord']) -> 'Chord':
        if isinstance(other, Chord):
            assert other in self
            return self.remove_or_ignore(other)
        elif other in digit_keys:
            return self - chord(only=other)
        elif other in all_keys:
            return self - Chord(frozenset((cast(Key, other),)))
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return hash(self.keys)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Chord):
            return self.keys == other.keys
        else:
            return NotImplemented

    def __ne__(self, other: object) -> bool:
        return not (self == other)


@overload
def chord(chord: ChordCls, *, ty: Type[ChordCls]) -> ChordCls: ...
@overload
def chord(chord: str, *, ty: Type[ChordCls]) -> ChordCls: ...
@overload
def chord(*args: Union[Key, Digit], ty: Type[ChordCls]) -> ChordCls: ...
@overload
def chord(*, only: Union[Key, Digit], ty: Type[ChordCls]) -> ChordCls: ...
@overload
def chord(chord: Chord) -> Chord: ...
@overload
def chord(chord: str) -> Chord: ...
@overload
def chord(*args: Union[Key, Digit]) -> Chord: ...
@overload
def chord(*, only: Union[Key, Digit]) -> Chord: ...

def chord(
    *args: Union[str, ChordCls],
    ty: Optional[Type[ChordCls]]=None,
    **kwargs: Union[str, ChordCls]
) -> ChordCls:
    converted_ty: Type[ChordCls] = ty if ty is not None else Chord

    if "only" in kwargs:
        # Only assertions since this is already restricted via overloading, so
        # this is just an internal sanity check
        assert not args
        assert len(kwargs) == 1

        only: Union[Key, Digit] = cast(Union[Key, Digit], kwargs["only"])
        assert only in all_keys or only in digit_keys

        if only in digit_keys:
            return chord("#", cast(Digit, only), ty=converted_ty)
        else:
            return converted_ty(frozenset((cast(Key, only),)))
    elif kwargs:  # `chord(chord=....)`
        # Only assertions since this is already restricted via overloading, so
        # this is just an internal sanity check
        assert not args
        assert set(kwargs.keys()) == {"chord"}

        return chord(kwargs["chord"], ty=converted_ty)
    elif len(args) == 1:
        if isinstance(args[0], str):
            return converted_ty.parse(args[0])
        else:
            return args[0]
    else:
        out = (
            frozenset((number_bar,))
            if set(args) & set(digit_keys)
            else frozenset()
        ) | frozenset(
            digit_keys[cast(Digit, i)] if i in digit_keys else i
            for i in args
        )

        # Only an assertion since this is already restricted via overloading,
        # so this is just an internal sanity check
        # Check that only the correct keys are used:
        assert out <= frozenset(all_keys)

        return converted_ty(cast(FrozenSet[Key], out))


Input = Tuple[Chord, ...]


def combine_single_chords(a: Input, b: Input) -> Input:
    assert len(a) == len(b) == 1
    return (a[0] + b[0],)


def concat_inputs(a: Input, b: Input) -> Input:
    return a + b


def begin_input_with(
    prefix: Union[str, Chord, Input]
) -> Callable[[Input], Input]:
    prefix_as_input = prefix if isinstance(prefix, tuple) else (chord(prefix),)
    return lambda x: prefix_as_input + x


def end_input_with(
    suffix: Union[str, Chord, Input]
) -> Callable[[Input], Input]:
    suffix_as_input = suffix if isinstance(suffix, tuple) else (chord(suffix),)
    return lambda x: x + suffix_as_input


def combine_first_chord(
    with_chord: Union[str, Chord]
) -> Callable[[Input], Input]:
    converted_chord = chord(with_chord)
    return lambda x: (x[0] + converted_chord,) + x[1:]


def to_input(x: Union[str, Chord, Input]) -> Input:
    return x if isinstance(x, tuple) else (chord(x),)


class Dictionary(object):
    elements: Dict[Input, str]

    def __init__(self, elements: Dict[Input, str]) -> None:
        self.elements = elements

    def copy(self) -> 'Dictionary':
        return Dictionary(self.elements.copy())

    def cross_product(
        self,
        other: 'Dictionary',
        *,
        key: Callable[[Input, Input], Input]=concat_inputs,
        value: Callable[[str, str], str]=lambda l, r: l + r,
    ) -> 'Dictionary':
        K = TypeVar("K")
        V = TypeVar("V")
        def checked_dict(items: Iterable[Tuple[K, V]]) -> Dict[K, V]:
            out: Dict[K, V] = {}
            for k, v in items:
                if k in out:
                    assert out[k] == v
                out[k] = v

            return out

        return Dictionary(checked_dict(
            (key(k1, k2), value(v1, v2))
            for k1, v1 in self.elements.items()
            for k2, v2 in other.elements.items()
        ))

    def keys_for(self, value: str) -> List[Input]:
        return [k for k, v in self.elements.items() if v == value]

    def to_plover_dict(self) -> Dict[str, str]:
        return {
            "/".join(i.plover_str for i in k): v
            for k, v in self.elements.items()
        }

    def map(
        self,
        *,
        keys: Callable[[Input], Input]=lambda x: x,
        values: Callable[[str], str]=lambda x: x
    ) -> 'Dictionary':
        return Dictionary({
            keys(k): values(v)
            for k, v in self.elements.items()
        })

    def __add__(self, other: 'Dictionary') -> 'Dictionary':
        out = self.elements.copy()
        for k, v in other.elements.items():
            if k in out:
                assert out[k] == v
            out[k] = v

        return Dictionary(out)

    def __sub__(self, other: Iterable[Input]) -> 'Dictionary':
        out = self.elements.copy()

        for i in other:
            try:
                del out[i]
            except KeyError:
                raise ValueError(
                        f"Removing {i!r} from this dictionary which doesn't " +
                        "contain it"
                    )

        return Dictionary(out)

    def __getitem__(self, key: Union[str, Chord, Input]) -> str:
        return self.elements[to_input(key)]

    def __setitem__(self, key: Union[str, Chord, Input], value: str) -> None:
        self.elements[to_input(key)] = value

    def __repr__(self) -> str:
        return "Dictionary(\n{})".format(
            "".join(
                "  {}: {!r},\n".format("/".join(str(i) for i in k), v)
                for k, v in self.elements.items()
            )
        )


def to_dict_key(x: Union[str, Chord, Input]) -> Union[str, Chord, Input]:
    return x


def dictionary(
    items: Union[
        Dict[Union[str, Chord, Input], str],  # The input can be a full dict
        Iterable[Tuple[Union[str, Chord, Input], str]]  # or an iterable for one
    ]
) -> Dictionary:
    dict_items = items.items() if isinstance(items, dict) else items
    return Dictionary({to_input(k): v for k, v in dict_items})


def dict_with_asterisk(dictionary: Dictionary) -> Dictionary:
    return dictionary.map(
        keys=lambda x: (
            (x[0].combine_nonoverlapping(chord(only=asterisk)),) + x[1:]
        ),
    )


# A few default dictionaries:

# Numbers:
single_digit_only = dictionary((Chord.digit(i), str(i)) for i in range(10))
double_digit_only = dictionary(
    (Chord.digit(i) + Chord.digit(j), str(i) + str(j))
    for i in range(10)
    for j in range(10)
    if in_order(to_key(i), to_key(j))
) + dictionary(
    (Chord.digit(i) + Chord.digit(j) + chord("E", "U"), str(i) + str(j))
    for i in range(10)
    for j in range(10)
    if in_order(to_key(j), to_key(i))
) + dictionary((Chord.digit(i) + "-D", str(i) * 2) for i in range(10))
hundred00 = dictionary({to_dict_key("0D"): "100"})
double_digit_only_hundred00 = (
    double_digit_only - hundred00.elements.keys() + hundred00
)
hundred1z = dictionary({to_dict_key("1-Z"): "100"})
double_digit_only_hundred1z = double_digit_only + hundred1z
single_and_double_digit = single_digit_only + double_digit_only
single_and_double_digit_hundred00 = (
    single_digit_only + double_digit_only_hundred00
)
single_and_double_digit_hundred1z = (
    single_digit_only + double_digit_only_hundred1z
)
hundreds = dictionary((Chord.digit(i) + "-Z", str(i) + "00") for i in range(10))
numbers = single_and_double_digit + hundreds

# Fingertyping
fingertyping_lowercase_no_asterisk = dictionary({
    to_dict_key("A"): "a",
    "PW": "b",
    "KR": "c",
    "TK": "d",
    "E": "e",
    "TP": "f",
    "TKPW": "g",
    "H": "h",
    "EU": "i",
    "SKWR": "j",
    "K": "k",
    "HR": "l",
    "PH": "m",
    "TPH": "n",
    "O": "o",
    "P": "p",
    "KW": "q",
    "R": "r",
    "S": "s",
    "T": "t",
    "U": "u",
    "SR": "v",
    "W": "w",
    "KP": "x",
    "KWR": "y",
    "STKPW": "z",
})
fingertyping_uppercase_no_p_no_asterisk = (
    fingertyping_lowercase_no_asterisk.map(values=str.upper)
)
fingertyping_uppercase_p_no_asterisk = (
    fingertyping_uppercase_no_p_no_asterisk.map(
        keys=combine_first_chord(chord(only="-P")),
    )
)
fingertyping_no_asterisk = (
    fingertyping_lowercase_no_asterisk + fingertyping_uppercase_p_no_asterisk
)
fingertyping_lowercase = dict_with_asterisk(fingertyping_lowercase_no_asterisk)
fingertyping_uppercase_no_p = dict_with_asterisk(
    fingertyping_uppercase_no_p_no_asterisk
)
fingertyping_uppercase_p = dict_with_asterisk(
    fingertyping_uppercase_p_no_asterisk
)
fingertyping = dict_with_asterisk(fingertyping_no_asterisk)