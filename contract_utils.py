from algosdk import *
from pyteal import *
from algosdk.logic import get_application_address

from time import time, sleep


def approval_contract():
    on_create = Approve()
    on_txn = Seq(
        If(Gtxn[Txn.group_index()-Int(1)].amount()
           >= Int(1000000)).Then(
            Approve()
        ).Else(
            Reject()
        ))
    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.NoOp, on_txn]
    )
    return program


# Define our ClearState Program.
def clearstate_contract():
    return Return(Int(1))


def create_contract(bank_address, bank_key, appl_address, coll_address, loan_amount, time_loan_close):

    # set global variables
    coll_amount = 0.2 * loan_amount

    startTime = int(time())
    endTime = startTime + time_loan_close*60
    endTimeColl = startTime + 10000

    app_args = [
        encoding.decode_address(bank_address),
        encoding.decode_address(appl_address),
        encoding.decode_address(coll_address),
        loan_amount.to_bytes(8, "big"),
        coll_amount.to_bytes(8, "big"),
        startTime.to_bytes(8, "big"),
        endTimeColl.to_bytes(8, "big"),
        endTime.to_bytes(8, "big"),
    ]

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

    approval_teal = compileTeal(approval_contract(), Mode.Application, version=5)
    clearstate_teal = compileTeal(clearstate_contract(), Mode.Application, version=5)
    # Next compile our TEAL to bytecode. (it's returned in base64)
    approval_b64 = algod_client.compile(approval_teal)['result']
    clearstate_b64 = algod_client.compile(clearstate_teal)['result']
    # Lastly decode the base64.
    approval_prog = encoding.base64.b64decode(approval_b64)
    clearstate_prog = encoding.base64.b64decode(clearstate_b64)

    # Create a transaction to deploy the contract
    # Obtain the current network suggested parameters.
    sp = algod_client.suggested_params()
    sp.flat_fee = True
    sp.fee = constants.MIN_TXN_FEE
    # Create an application call transaction without an application ID (aka Create)
    txn = future.transaction.ApplicationCreateTxn(
        bank_address,
        bank_key,
        future.transaction.OnComplete.NoOpOC,
        approval_prog,
        clearstate_prog,
        future.transaction.StateSchema(0, 0),
        future.transaction.StateSchema(0, 0),
        app_args=app_args
    )

    # launch contract on chain
    txid = algod_client.send_transaction(txn.sign(sk))
    future.transaction.wait_for_confirmation(algod_client, txid)
    response = algod_client.pending_transaction_info(txid)

    # get relevant parameters from contract
    appID = response['application-index']
    appAddr = get_application_address(response['application-index'])

    payTxn = future.transaction.PaymentTxn(
        sender=bank_address,
        receiver=appAddr,
        amt=loan_amount,
        sp=sp
    )

    appCallTxn = future.transaction.ApplicationCallTxn(
        sender=bank_address,
        index=appID,
        on_complete=future.transaction.OnComplete.NoOpOC,
        sp=sp
    )

    transaction.assign_group_id([payTxn, appCallTxn])

    signedPayTxn = payTxn.sign(bank_key)
    signedAppCallTxn = appCallTxn.sign(bank_key)

    algod_client.send_transactions([signedPayTxn, signedAppCallTxn])

    future.transaction.wait_for_confirmation(algod_client, appCallTxn.get_txid())

    return appID, appAddr


def pay2contract(origin, target, amount, origin_key):

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

    sp = algod_client.suggested_params()
    sp.flat_fee = True
    sp.fee = constants.MIN_TXN_FEE

    payTxn = future.transaction.PaymentTxn(
        sender=origin,
        receiver=target,
        amt=amount,
        sp=sp
    )

    appCallTxn = future.transaction.ApplicationCallTxn(
        sender=origin,
        index=appID,
        on_complete=future.transaction.OnComplete.NoOpOC,
        sp=sp
    )

    transaction.assign_group_id([payTxn, appCallTxn])

    signedPayTxn = payTxn.sign(origin_key)
    signedAppCallTxn = appCallTxn.sign(origin_key)

    algod_client.send_transactions([signedPayTxn, signedAppCallTxn])

    future.transaction.wait_for_confirmation(algod_client, appCallTxn.get_txid())

