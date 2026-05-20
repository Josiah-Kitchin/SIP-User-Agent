from dataclasses import dataclass
from enum import Enum


class SIPParseException(Exception):
    def __init__(self, message: str):
        super().__init__("Failed to parse SIP message: " + message)


class SIPRequestType(Enum):
    INVITE = "INVITE"
    ACK = "ACK"
    BYE = "BYE"
    CANCEL = "CANCEL"
    REGISTER = "REGISTER"
    OPTIONS = "OPTIONS"


class SIPResponseType(Enum):
    RINGING = 180


class Transport(Enum):
    UDP = "UDP"
    TCP = "TCP"


class HeaderLine: ...


class HeaderType(Enum):
    VIA = "Via"
    MAX_FORWARDS = "Max-Forwards"
    TO = "To"
    FROM = "From"
    CALL_ID = "Call-ID"
    CSEQ = "CSeq"
    CONTACT = "Contact"
    CONTENT_TYPE = "Content-Type"
    CONTENT_LENGTH = "Content-Length"


@dataclass
class ViaHeaderLine(HeaderLine):
    transport: Transport
    host: str
    branch: str


@dataclass
class MaxForwardsLine(HeaderLine):
    val: int


@dataclass
class ToHeaderLine(HeaderLine):
    name: str
    address: str
    tag: str | None


@dataclass
class FromHeaderLine(HeaderLine):
    name: str
    address: str
    tag: str


@dataclass
class CallIDHeaderLine(HeaderLine):
    address: str


@dataclass
class CSeqHeaderLine(HeaderLine):
    seq_num: int
    seq_type: SIPRequestType


@dataclass
class ContactHeaderLine(HeaderLine):
    address: str


@dataclass
class ContentTypeHeaderLine(HeaderLine):
    content_type: str


@dataclass
class ContentLengthHeaderLine(HeaderLine):
    content_len: int


@dataclass
class SIPRequest:
    req_type: SIPRequestType
    headers: dict[HeaderType, HeaderLine]
    unknown_headers: dict[str, str]


@dataclass
class SIPResponse:
    res_type: SIPResponseType
    headers: dict[HeaderType, HeaderLine]
    unknown_headers: dict[str, str]


def parse_via_header_line(header_value: str) -> ViaHeaderLine:
    split_header = header_value.split()

    _, _, transport = split_header[0].split("/")

    host, branch = split_header[1].split(";")

    branch_val = branch.split("=")[1]

    if not host or not branch_val:
        raise ValueError("Expected value missing")

    return ViaHeaderLine(
        transport=Transport(transport),
        host=host,
        branch=branch_val,
    )


def get_str_between(value: str, open_char: str, close_char: str) -> str:
    open_idx = 0
    close_idx = 0
    need_open = True
    for i in range(len(value)):
        if need_open and value[i] == open_char:
            open_idx = i
            need_open = False

        elif not need_open and value[i] == close_char:
            close_idx = i
            break

    if close_idx <= open_idx:
        raise ValueError("Missing open or closing character")
    return value[open_idx + 1 : close_idx]


def parse_to_header_line(header_value: str) -> ToHeaderLine:
    name = get_str_between(header_value, '"', '"')
    rest = header_value[len(name) + 1 :]
    address = get_str_between(rest, "<", ">")
    tag = None
    tag_split = header_value.split(";")
    if len(tag_split) > 1:
        tag = tag_split[1].split("=")[1]
    return ToHeaderLine(name=name, address=address, tag=tag)


def parse_from_header_line(header_value: str) -> FromHeaderLine:
    name = get_str_between(header_value, '"', '"')
    rest = header_value[len(name) + 1 :]
    address = get_str_between(rest, "<", ">")
    tag_split = header_value.split(";")
    tag = tag_split[1].split("=")[1]
    return FromHeaderLine(name=name, address=address, tag=tag)


def parse_c_seq_header_line(header_value: str) -> CSeqHeaderLine:
    seq, seq_type = header_value.split()
    return CSeqHeaderLine(seq_num=int(seq), seq_type=SIPRequestType[seq_type])


def parse_contact_header_line(header_value: str) -> ContactHeaderLine:
    return ContactHeaderLine(address=get_str_between(header_value, "<", ">"))


def parse_headers(
    header_lines: list[str],
) -> tuple[dict[HeaderType, HeaderLine], dict[str, str]]:
    parsed_headers = {}
    unknown_headers = {}
    for line in header_lines:
        split_header = line.split(":", 1)
        split_header[0] = split_header[0].strip()

        try:
            header_type_str = split_header[0]
            header_value = "".join(split_header[1:])
        except IndexError:
            raise SIPParseException(f"No header type found for line: {line}")

        try:
            header_type = HeaderType(header_type_str)
        except ValueError:
            unknown_headers[header_type_str] = header_value
            continue

        try:
            match header_type:
                case HeaderType.VIA:
                    parsed_headers[header_type] = parse_via_header_line(header_value)
                case HeaderType.MAX_FORWARDS:
                    parsed_headers[header_type] = MaxForwardsLine(int(header_value))
                case HeaderType.TO:
                    parsed_headers[header_type] = parse_to_header_line(header_value)
                case HeaderType.FROM:
                    parsed_headers[header_type] = parse_from_header_line(header_value)
                case HeaderType.CALL_ID:
                    parsed_headers[header_type] = header_value
                case HeaderType.CSEQ:
                    parsed_headers[header_type] = parse_c_seq_header_line(header_value)
                case HeaderType.CONTACT:
                    parsed_headers[header_type] = parse_contact_header_line(
                        header_value
                    )
                case HeaderType.CONTENT_TYPE:
                    parsed_headers[header_type] = ContentTypeHeaderLine(header_value)
                case HeaderType.CONTENT_LENGTH:
                    parsed_headers[header_type] = ContentLengthHeaderLine(
                        int(header_value)
                    )

        except Exception as e:
            raise SIPParseException(
                f"Header parse failure for type: {header_type.value}, \
                                    reason: {e} for line: {line}"
            )
    return parsed_headers, unknown_headers


def parse_sip_request(msg: str) -> SIPRequest:
    """
    Parse a SIP request header

    msg: SIP request
        line 1: request line
        line 2..n: headers (optional)

    raises SIPParseException on request that is malformed or missing fields
    """
    lines = msg.splitlines()
    try:
        request_line = lines[0].split()
        request_type = request_line[0]
    except Exception:
        raise SIPParseException(f"Request line parse failure")
    headers, unknown_headers = parse_headers(lines[1:])
    return SIPRequest(
        req_type=SIPRequestType(request_type),
        headers=headers,
        unknown_headers=unknown_headers,
    )


def parse_sip_response(msg: str) -> SIPResponse:
    """
    Parse a SIP response header

    msg: SIP response
        line 1: request line
        line 2..n: headers (optional)

    raises SIPParseException on response that is malformed or missing fields
    """
    lines = msg.splitlines()
    response_code = int(lines[0].split()[1])
    headers, unknown_headers = parse_headers(lines[1:])
    return SIPResponse(
        res_type=SIPResponseType(response_code),
        headers=headers,
        unknown_headers=unknown_headers,
    )



