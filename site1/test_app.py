from pathlib import Path

import pytest

from site1.accounts import find_account_by_username


@pytest.fixture
def client():
   from .site1_app import app
   return app.test_client()


def test_transfer(client):
   alice_token = Path(__file__).parent.joinpath('token_alice').read_text()
   alice = find_account_by_username('alice')

   client.set_cookie("token", alice_token)
   resp = client.post('/accounts/transfer', data={'to': 'bob', 'amount': 100},
                      headers={"Cookie": f"token={alice_token}"}, )
   assert resp.status_code == 200
   assert alice.balance == 900
