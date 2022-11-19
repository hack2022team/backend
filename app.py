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
    appID, contractAddr = contract_utils.create_contract(bank_address=,
                                   bank_key=,
                                   appl_address=info['inputWallet'],
                                   coll_address=None,
                                   loan_amount=info['inputSum'],
                                   time_loan_close=info['inputDuration'])
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
