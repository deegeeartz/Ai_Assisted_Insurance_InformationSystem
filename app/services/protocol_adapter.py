import dicttoxml
import xmltodict
import json
from fastapi.responses import Response


def dict_to_soap_xml(data: dict, root_name: str = "UnderwriteResponse") -> str:
    """Convert a dictionary to a SOAP XML envelope."""
    soap_envelope = {
        "soap:Envelope": {
            "@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "soap:Header": {},
            "soap:Body": {
                root_name: data,
            },
        }
    }
    return xmltodict.unparse(soap_envelope, pretty=True)


def soap_xml_to_dict(xml_string: str) -> dict:
    """Parse a SOAP XML envelope back to a dictionary."""
    parsed = xmltodict.parse(xml_string)
    body = parsed.get("soap:Envelope", {}).get("soap:Body", {})
    return body


def create_soap_response(data: dict, root_name: str = "UnderwriteResponse") -> Response:
    """Create a FastAPI Response object with SOAP XML content."""
    xml_content = dict_to_soap_xml(data, root_name)
    return Response(
        content=xml_content,
        media_type="application/soap+xml",
    )
