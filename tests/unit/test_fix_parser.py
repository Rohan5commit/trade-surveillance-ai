from src.ingestion.fix_parser import parse_fix_message


def test_parse_fix_message_new_order() -> None:
    raw = "35=D|55=AAPL|54=1|38=100|44=190.5|1=acct-1|11=ord-1|60=20260225-10:10:10.100"
    event = parse_fix_message(raw)
    assert event is not None
    assert event.event_type == "new_order"
    assert event.symbol == "AAPL"
    assert event.account_id == "acct-1"
