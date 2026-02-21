from dataclasses import dataclass

from . import tokenlib

_accounts = {}


@dataclass
class Account:
   username: str
   balance: int
   token: str


def find_account_by_username(username):
   return _accounts.get(username)


def find_account_by_token(token):
   username = tokenlib.decode_token(token)
   if username:
      return _accounts.get(username)
   return None


def prepare_account(username, balance):
   token = tokenlib.encode_username(username)
   account = Account(username, balance, token)
   _accounts[username] = account
   return account
