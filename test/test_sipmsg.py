import sipmsg
import pytest


def test_parse_to_header_line():
    to_header = sipmsg.parse_to_header_line('"Bob Smith" <sip:bob@example.com>')
    assert to_header.name == "Bob Smith"
    assert to_header.address == "sip:bob@example.com"
    assert to_header.tag is None

    to_header_with_tag = sipmsg.parse_to_header_line(
        '"Bob Smith" <sip:bob@example.com>;tag=abc'
    )
    assert to_header_with_tag.tag == "abc"


def test_parse_to_header_line_malformed():
    with pytest.raises(Exception):
        _ = sipmsg.parse_to_header_line('"Bob Smith" sip:bob@example.com>')


def test_parse_bad_to_header_line_missing():
    with pytest.raises(Exception):
        _ = sipmsg.parse_to_header_line('"Bob Smith"')


def test_parse_via_header_line():
    via_header = sipmsg.parse_via_header_line(
        "SIP/2.0/UDP 192.168.55.1:7800;branch=z9hG4bK776asdhds"
    )

    assert via_header.transport == sipmsg.Transport.UDP
    assert via_header.host == "192.168.55.1:7800"
    assert via_header.branch == "z9hG4bK776asdhds"


def test_parse_via_header_line_malformed():
    with pytest.raises(Exception):
        _ = sipmsg.parse_via_header_line(
            "SIP/2.0/UDP 192.168.55.1:7800;branchz9hG4bK776asdhds"
        )


def test_parse_via_header_line_missing():
    with pytest.raises(Exception):
        _ = sipmsg.parse_via_header_line("SIP/2.0/UDP ;branch=z9hG4bK776asdhds")


def test_parse_from_header_line():
    from_header = sipmsg.parse_from_header_line(
        '"Bob Smith" <sip:bob@example.com>;tag=abc'
    )

    assert from_header.address == "sip:bob@example.com"
    assert from_header.name == "Bob Smith"
    assert from_header.tag == "abc"


def test_parse_from_header_line_malformed():
    with pytest.raises(Exception):
        _ = sipmsg.parse_from_header_line('"Bob Smith <sip:bob@example.com>;tag=abc')


def test_parse_from_header_line_missing():
    with pytest.raises(Exception):
        _ = sipmsg.parse_from_header_line("<sip:bob@example.com>;tag=abc")


def test_parse_c_seq_header_line():
    seq_header = sipmsg.parse_c_seq_header_line("10 INVITE")
    assert seq_header.seq_num == 10
    assert seq_header.seq_type == sipmsg.SIPRequestType.INVITE


def test_parse_c_seq_header_line_malformed():
    with pytest.raises(Exception):
        _ = sipmsg.parse_c_seq_header_line("hello INVITE")


def test_parse_c_seq_header_line_missing():
    with pytest.raises(Exception):
        _ = sipmsg.parse_c_seq_header_line("10")


def test_contact_header_line():
    contact_header = sipmsg.parse_contact_header_line(" <sip:bob@192.168.55.1:5000>")
    assert contact_header.address == "sip:bob@192.168.55.1:5000"


def test_contact_header_line_malformed():
    with pytest.raises(Exception):
        _ = sipmsg.parse_contact_header_line(" <sip:bob@192.168.55.1:5000")


def test_parse_sip_request():
    msg = (
        "INVITE sip:bob@192.168.1.100:5060 SIP/2.0\n"
        + "Via: SIP/2.0/UDP 192.168.55.1:7800;branch=z9hG4bk776asdhds\n"
        + 'From: "Bob Smith" <sip:bob@example.com>;tag=abc\n'
    )

    req = sipmsg.parse_sip_request(msg)
    assert req.req_type == sipmsg.SIPRequestType.INVITE
    assert sipmsg.HeaderType.VIA in req.headers
    assert sipmsg.HeaderType.FROM in req.headers


def test_parse_sip_response():

    msg = (
        "SIP/2.0 180 Ringing\n"
        + "Via: SIP/2.0/UDP 10.0.0.50:5060;branch=z9hG4bK776asdhds\n"
        + 'To: "Bob Smith" <sip:bob@example.com>;tag=a6c85cf\n'
        + 'From: "Alice Jones" <sip:alice@example.com>;tag=1928301774\n'
        + "Call-ID: a84b4c76e66710@10.0.0.50\n"
        + "CSeq: 1 INVITE\n"
        + "Contact: <sip:bob@192.168.1.100:5060>\n"
        + "Content-Length: 0\n"
        + "Unknown: hi\n"
    )

    res = sipmsg.parse_sip_response(msg)
    assert res.res_type == sipmsg.SIPResponseType.RINGING

    for header in [
        sipmsg.HeaderType.VIA,
        sipmsg.HeaderType.TO,
        sipmsg.HeaderType.CALL_ID,
        sipmsg.HeaderType.CSEQ,
        sipmsg.HeaderType.CONTACT,
        sipmsg.HeaderType.CONTENT_LENGTH,
    ]:
        assert header in res.headers

    assert " hi" == res.unknown_headers["Unknown"]


