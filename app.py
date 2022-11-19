import json

from flask import Flask, request, redirect
from jinja2 import Environment, PackageLoader, select_autoescape
import db_handler
import contract_utils

from algosdk import *
from pyteal import *
from algosdk.logic import get_application_address
from base64 import b64decode

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

@app.route('/status')
def loan_overview():
    loans = db_handler.get_open_loans()
    givers = db_handler.get_giver_accounts()
    c_data = {}
    for l in loans:
        c_data[l['escrow_wallet']] = get_contract_info(l['escrow_wallet'])
    template = env.get_template("loan_overview.html")
    return template.render(loans=loans, givers=givers, c_data=c_data)

@app.route('/wallet')
def loan_repayment():
    loans = db_handler.get_open_loans()
    receivers = db_handler.get_receiver_accounts()
    c_data = {}
    for l in loans:
        c_data[l['escrow_wallet']] = get_contract_info(l['escrow_wallet'])
    template = env.get_template("wallet.html")
    return template.render(loans=loans, receivers=receivers, c_data=c_data)


@app.route('/submit',  methods=['GET'])
def receive_loan_request():
    print("submit")
    # info=request.form
    info = request.args.to_dict()
    print(request.args.to_dict())
    # Boilerplate init for Algo sandbox
    algod_token = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'  # Algod API Key
    algod_addr = 'http://localhost:4001'  # Algod Node Address
    algod_header = {
        'User-Agent': 'Minimal-PyTeal-SDK-Demo/0.1',
        'X-API-Key': algod_token
    }
    algod_client = v2client.algod.AlgodClient(
        algod_token,
        algod_addr,
        algod_header
    )
    print("algo client maybe ready")
    try:
        algod_client.status()
    except error.AlgodHTTPError:
        quit(f"algod node connection failure. Check the host and API key are correct.")
    print("algo client ready")
    appID, contractAddr = contract_utils.create_contract(
        bank_address='VELO7H2K7D72I2TIKZFPVMQH57PUD4R5DXXBA4Y4SMHBZQS42NJHNQS2YI',
        bank_key='7j2aXRN5L/s4f1EJOxKAdaMBkNG/Zhglbox3l6oHyPOpFu+fSvj/pGpoVkr6sgfv30HyPR3uEHMckw4cwlzTUg==',
        appl_address=info['inputWallet'],
        coll_address="",
        loan_amount=int(info['inputSum'])*1000*1000,
        time_loan_close=int(info['inputDuration']),
        client=algod_client)
    print(appID)
    print(contractAddr)
    db_handler.write_to_database(info, contractAddr, appID)
    print("Wrote to DB")
    return "Submitted"


@app.route('/sendToEscrow', methods=['GET'])
def give_collateral():
    # Boilerplate init for Algo sandbox
    algod_token = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'  # Algod API Key
    algod_addr = 'http://localhost:4001'  # Algod Node Address
    algod_header = {
        'User-Agent': 'Minimal-PyTeal-SDK-Demo/0.1',
        'X-API-Key': algod_token
    }
    algod_client = v2client.algod.AlgodClient(
        algod_token,
        algod_addr,
        algod_header
    )

    res = request.args.to_dict()
    contract_utils.pay2contract(res['sourceId'], res['destinationId'], res['amount'],
                                db_handler.get_giver_key(res['sourceId']),
                                algod_client,
                                db_handler.get_appid(res['destinationId']) )
    # Hier funktion eingeben um an Escrow zu überweisen
    return "Collateral provided"


def get_contract_info(destinationId):
    # Boilerplate init for Algo sandbox
    algod_token = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'  # Algod API Key
    algod_addr = 'http://localhost:4001'  # Algod Node Address
    algod_header = {
        'User-Agent': 'Minimal-PyTeal-SDK-Demo/0.1',
        'X-API-Key': algod_token
    }
    algod_client = v2client.algod.AlgodClient(
        algod_token,
        algod_addr,
        algod_header
    )

    appID = db_handler.get_appid(destinationId)
    info = algod_client.application_info(appID)

    states = ['loan unfunded',
              'collateral outstanding',
              'loan outstanding',
              'loan repayed']

    info_dict = {}
    for row in info['params']['global-state']:
        row['key'] = b64decode(row['key'])
        key = row['key'].decode()
        if row['value']['type'] == 2:
            value = row['value']['uint']
        elif row['value']['type'] == 1:
            value = row['value']['bytes']
        if key == 'state':
            info_dict[key] = states[value]
        else:
            info_dict[key] = value

    return info_dict


if __name__ == '__main__':
    app.run()
