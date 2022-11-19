import json

from flask import Flask, request
from jinja2 import Environment, PackageLoader, select_autoescape
import db_handler
import contract_utils

app = Flask(__name__)

env = Environment(
    loader=PackageLoader("app"),
    autoescape=select_autoescape()
)


@app.route('/give')
def show_loan_giving():
    loans = db_handler.get_open_loans()
    givers = db_handler.get_giver_accounts()
    template = env.get_template("give_collateral.html")
    return template.render(loans=loans, givers=givers)


@app.route('/take')
def show_loan_taking():
    template = env.get_template("receive_collateral.html")
    return template.render()


@app.route('/submit',  methods=['POST'])
def receive_loan_request():
    db_handler.write_to_database(request.form, "Escrow")
    info=request.form
    # Boilerplate init for Algo sandbox
    algod_token  = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' # Algod API Key
    algod_addr   = 'http://localhost:4001' # Algod Node Address
    algod_header = {
        'User-Agent': 'Minimal-PyTeal-SDK-Demo/0.1',
        'X-API-Key': algod_token
    }
    algod_client = v2client.algod.AlgodClient(
        algod_token,
        algod_addr,
        algod_header
    )
    try:
        algod_client.status()
    except error.AlgodHTTPError:
        quit(f"algod node connection failure. Check the host and API key are correct.")

    appID, contractAddr = contract_utils.create_contract(bank_address=,
                                                         bank_key=,
                                                         appl_address=info['inputWallet'],
                                                         coll_address=None,
                                                         loan_amount=info['inputSum'],
                                                         time_loan_close=info['inputDuration'],
                                                         client=algod_client)
    print(appID)
    print(contractAddr)

    return "Submitted"

@app.route('/sendToEscrow', methods=['POST'])
def give_collateral():
    print(request.get_json())
    # Hier funktion eingeben um an Escrow zu überweisen
    return "Collateral provided"

if __name__ == '__main__':
    app.run()
