import mdformat
import pytest
from mdformat_twospace.double_space import double_space


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # sentence-final punctuation gets a second space
        ("End of sentence. Beginning of next.", "End of sentence.  Beginning of next."),
        ("A colon: as well", "A colon:  as well"),
        ("Yes! No way", "Yes!  No way"),
        ("Really? Maybe", "Really?  Maybe"),
        ('He said "go." Then left.', 'He said "go."  Then left.'),
        ("Wait... beginning", "Wait...  beginning"),
        # false periods — left untouched
        ("Mr. Smith went home.", "Mr. Smith went home."),
        ("See e.g. this case here.", "See e.g. this case here."),
        ("J. R. R. Tolkien wrote it.", "J. R. R. Tolkien wrote it."),
        ("Pi is 3.14 here.", "Pi is 3.14 here."),
        # end of line / no following text — no trailing whitespace introduced
        ("Ends here.", "Ends here."),
        ("Line one.\nLine two.", "Line one.\nLine two."),
    ],
)
def test_double_space(text: str, expected: str) -> None:
    result = double_space(text, None, None)

    assert result == expected


# Node-boundary cases run through the full formatter, since the punctuation and
# the start of the next sentence land in different inline nodes.


def test_double_space_into_following_span() -> None:
    # case A: the colon ends a text node; a strong span begins the next sentence.
    result = mdformat.text(
        '- Andrew: __"Family and fun. The overarching theme."__\n', extensions=["twospace"]
    )

    assert "Andrew:  " in result
    assert "fun.  The" in result


def test_double_space_out_of_preceding_span() -> None:
    # case B: the sentence ends inside the bold span and continues after it.
    result = mdformat.text("**Done.** Next sentence follows.\n", extensions=["twospace"])

    assert "  Next" in result


def test_no_double_space_after_code_span() -> None:
    # a period inside inline code is not a sentence boundary.
    result = mdformat.text("`value.` next token here.\n", extensions=["twospace"])

    assert "  next" not in result
