from app.services.quotes import locate_quote

CONTENT = "Timesheets are due every Friday by 5:00 PM.\nRound to the nearest quarter hour."


def test_exact_quote_is_returned_as_is():
    assert locate_quote("due every Friday", CONTENT) == "due every Friday"


def test_case_and_whitespace_differences_return_the_source_spelling():
    assert locate_quote("DUE   every\nfriday", CONTENT) == "due every Friday"
    assert locate_quote("5:00 pm.\nround", CONTENT) == "5:00 PM.\nRound"


def test_later_texts_are_searched_too():
    assert locate_quote("Late timesheets", CONTENT, "Late timesheets and questions") == "Late timesheets"


def test_missing_quotes_are_not_found():
    assert locate_quote("due every Monday", CONTENT) is None
    assert locate_quote("due", "") is None


def test_empty_or_blank_quotes_are_never_found():
    # The two copies this replaced disagreed here: grounding "found" an empty quote.
    assert locate_quote("", CONTENT) is None
    assert locate_quote("   \n", CONTENT) is None
