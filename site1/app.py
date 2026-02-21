import os
from pathlib import Path

from flask import Flask, make_response, request
from werkzeug.exceptions import Unauthorized

from . import accounts

app = Flask(__name__)


@app.errorhandler(Unauthorized)
def handle_unauthorized(e):
   return make_response(e.description, 401)


def make_unauthorized_response():
   response = make_response("Unauthorized", 401)
   response.set_cookie('token', 'unauthorized')
   return response


def authenticate_request(request):
   token = request.cookies.get('token')
   if not token:
      raise Unauthorized("缺少token")
   account = accounts.find_account_by_token(token)
   if not account:
      raise Unauthorized("无效的token")
   return account


@app.get('/accounts/me')
def me():
   account = authenticate_request(request)
   if not account:
      return make_unauthorized_response()
   return f"Hello {account.username}, your balance is {account.balance}"


@app.post('/accounts/transfer')
def transfer():
   sender = authenticate_request(request)
   recipient_username = request.form.get('recipient')
   amount = int(request.form.get('amount', 0))
   recipient = accounts.find_account_by_username(recipient_username)

   if not recipient:
      return f"Recipient {recipient_username} does not exist."
   if not sender:
      return f"需要指定amount"

   recipient.balance += amount
   sender.balance -= amount

   return f"Transferred {amount} to {recipient_username}. Your new balance is {sender.balance}"


def write_token(account_name, token):
   dir = Path("tokens")
   dir.mkdir(exist_ok=True)
   dir.joinpath(account_name).write_text(token)


if __name__ == '__main__':
   os.chdir(Path(__file__).parent)

   alice = accounts.prepare_account("alice", 1000)
   bob = accounts.prepare_account("bob", 1000)
   write_token(alice.username, alice.token)
   write_token(bob.username, bob.token)

   port = int(os.environ.get("PORT", 5001))
   app.run(debug=False, port=port)
