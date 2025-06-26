import json
import logging
import uuid
from http.server import BaseHTTPRequestHandler

from src.api_requests import check_auth, Request, OnlineScoreRequest, ClientsInterestsRequest
from src.scoring_service import get_score, get_interests
from src.store import Store

OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}


def method_handler(request_dict, ctx, store):
    try:
        body = request_dict.get("body", {})

        if not body:
            return {"error": "Empty request"}, INVALID_REQUEST

        if not check_auth(request_dict):
            return {"error": "Authentication failed"}, FORBIDDEN

        method = body.get("method")
        arguments = body.get("arguments", {})

        if not method:
            return {"error": "Method is required"}, INVALID_REQUEST

        if method == 'clients_interests':
            if not isinstance(arguments.get("client_ids"), list) or not arguments.get("client_ids"):
                return {"error": "client_ids must be non-empty list"}, INVALID_REQUEST

            try:
                request = ClientsInterestsRequest(arguments)
            except ValueError as e:
                return {"error": str(e)}, INVALID_REQUEST

            interests = {}
            for cid in request.client_ids:
                interests[str(cid)] = get_interests(store, cid)
            ctx["nclients"] = len(interests)
            return interests, OK

        elif method == 'online_score':
            try:
                request = OnlineScoreRequest(arguments)
            except ValueError as e:
                return {"error": str(e)}, INVALID_REQUEST

            if Request(request_dict).is_admin:
                score = 42
            else:
                score = get_score(
                    store,
                    phone=request.phone,
                    email=request.email,
                    first_name=request.first_name,
                    last_name=request.last_name,
                    gender=request.gender,
                    birthday=request.birthday,
                )

            ctx["has"] = [k for k, v in arguments.items() if v]
            return {"score": score}, OK

        else:
            return {"error": "Unknown method"}, NOT_FOUND

    except Exception as e:
        logging.exception("Handler error")
        return {"error": "Internal error"}, INTERNAL_ERROR


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {"method": method_handler}
    store= Store()

    def get_request_id(self, headers):
        return headers.get('X-Request-ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            request = json.loads(self.rfile.read(content_length))

        except Exception:
            code = BAD_REQUEST

        if request:
            try:
                request_body = request.get('body', {})
                headers = request.get('headers', {})
                path = self.path.strip("/")
                if path in self.router:
                    response, code = self.router[path]({"body": request_body, "headers": headers}, context, self.store)
                else:
                    code = NOT_FOUND
            except Exception as e:
                logging.error(f"Request failed: {str(e)}")
                code = INTERNAL_ERROR if code == OK else code

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response_data = {
            "code": code,
            "response": response if code == OK else None,
            "error": ERRORS.get(code, "Unknown Error") if code != OK else None
        }
        self.wfile.write(json.dumps(response_data).encode('utf-8'))
        return


def handle_online_score(request, arguments, context):
    if request.is_admin:
        return {"code": OK, "response": {"score": 42}}, context

    score = get_score(
        None,
        phone=arguments.get("phone"),
        email=arguments.get("email"),
        birthday=arguments.get("birthday"),
        gender=arguments.get("gender"),
        first_name=arguments.get("first_name"),
        last_name=arguments.get("last_name"),
    )

    context["has"] = [key for key, value in arguments.items() if value is not None]
    return {"code": OK, "response": {"score": score}}, context


def handle_clients_interests(arguments, context):
    client_ids = arguments.get("client_ids")
    if not client_ids or not isinstance(client_ids, list) or not client_ids:
        return {"code": INVALID_REQUEST,
                "error": "client_ids must be a non-empty list of integers"}, context

    if not all(isinstance(item, int) for item in client_ids):
        return {"code": INVALID_REQUEST,
                "error": "All client_ids must be integers"}, context

    interests = {
        str(client_id): get_interests(None, client_id)
        for client_id in client_ids
    }
    context["nclients"] = len(client_ids)
    return {"code": OK, "response": interests}, context
