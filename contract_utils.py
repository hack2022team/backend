from algosdk import *
from pyteal import *
from algosdk.logic import get_application_address

from time import time, sleep


def approval_contract():
    credit_giver_key = Bytes("credit_giver_key")
    credit_taker_key = Bytes("credit_taker_key")
    security_giver_key = Bytes("security_giver")
    security_giver_value = Bytes("security_giver_value")
    escrow_value = Bytes("escrow_value")
    security_giver_goal_sum = Bytes("security_giver_goal_sum")
    number_of_security_givers = Bytes("securty_giver")
    credit = Bytes("credit")
    interest_credit = Bytes("interest_credit")
    interest_security = Bytes("interest_security")
    security_start_time = Bytes("security_start")
    security_end_time = Bytes("securty_end")
    credit_start_time = Bytes("credit_start")
    credit_end_time = Bytes("credit_start")
    state = Bytes("state")

    # @Subroutine(TealType.none)
    # def transact(receiver: Expr, amount: Expr) -> Expr:
    #     return Seq(
    #         InnerTxnBuilder.Begin(),
    #         InnerTxnBuilder.SetFields(
    #             {
    #                 TxnField.type_enum: TxnType.Payment,
    #                 TxnField.amount: amount,
    #                 TxnField.receiver: receiver,
    #             }
    #         ),
    #         InnerTxnBuilder.Submit(),
    #     )

    on_create = Seq(
        App.globalPut(credit_giver_key, Bytes("VELO7H2K7D72I2TIKZFPVMQH57PUD4R5DXXBA4Y4SMHBZQS42NJHNQS2YI")),
        App.globalPut(credit_taker_key,
                      Bytes(b'\x1f\x83\x1d9\xda\x9dZH5Qt\xfb]L\t\x12\xe8{3\xb0\xb2\xaa\xe9^(\x88|{\xea!\xa7\xcb')),
        App.globalPut(security_start_time, Bytes("")),
        App.globalPut(security_giver_value, Int(0)),
        App.globalPut(escrow_value, Int(0)),
        App.globalPut(security_giver_goal_sum, Int(100000)),
        App.globalPut(credit, Int(500000)),
        App.globalPut(interest_credit, Int(0)),
        App.globalPut(interest_security, Int(0)),
        App.globalPut(security_end_time, Bytes("")),
        App.globalPut(credit_start_time, Bytes("")),
        App.globalPut(credit_end_time, Bytes("")),
        App.globalPut(state, Int(0)),
        Approve()
    )
    # The contract can be closed, if the escrow contains (100%+InterestRate)of Credit and (100%+InterestRate)of Security
    pay_credit_escrow_goal = (App.globalGet(credit) * (App.globalGet(interest_credit) + Int(100)) / Int(100)) + (
                App.globalGet(security_giver_goal_sum) * (App.globalGet(interest_security) + Int(100)) / Int(100))
    on_setup = Seq(
        App.globalPut(escrow_value, Add(App.globalGet(escrow_value), Gtxn[Txn.group_index() - Int(1)].amount())),
        If(App.globalGet(escrow_value) >= App.globalGet(credit)).Then(
            App.globalPut(state, Int(1))
        ),
        Approve()
    )
    on_security = Seq(
        # Todo: Stop if too late for security
        App.globalPut(escrow_value, Add(App.globalGet(escrow_value), Gtxn[Txn.group_index() - Int(1)].amount())),
        # Transmit credit if enough security
        If(App.globalGet(escrow_value) >= App.globalGet(security_giver_goal_sum)).Then(
            Seq(
                App.globalPut(state, Int(2)),
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.amount: App.globalGet(credit),
                        TxnField.receiver: App.globalGet(credit_taker_key),
                    }
                ),
                InnerTxnBuilder.Submit(),
                App.globalPut(escrow_value, Minus(App.globalGet(escrow_value), App.globalGet(credit)))
            )
        ),
        Approve(),
    )
    on_pay_credit = Seq(
        # Todo: Stop if too late for credit
        App.globalPut(escrow_value, Add(App.globalGet(escrow_value), Gtxn[Txn.group_index() - Int(1)].amount())),
        Approve()
    )
    pay_credit_goal = Add(App.globalGet(security_giver_goal_sum), App.globalGet(credit))
    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [App.globalGet(state) < Int(1), on_setup],
        [App.globalGet(state) < Int(2), on_security],
        [App.globalGet(state) < Int(3), on_pay_credit]
    )
    return program


# Define our ClearState Program.
def clearstate_contract():
    return Return(Int(1))


def create_contract(bank_address, bank_key, appl_address, coll_address, loan_amount, time_loan_close, client):

    # set global variables
    coll_amount = int(0.2 * loan_amount)

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

    approval_teal = compileTeal(approval_contract(), Mode.Application, version=5)
    clearstate_teal = compileTeal(clearstate_contract(), Mode.Application, version=5)
    # Next compile our TEAL to bytecode. (it's returned in base64)
    approval_b64 = client.compile(approval_teal)['result']
    clearstate_b64 = client.compile(clearstate_teal)['result']
    # Lastly decode the base64.
    approval_prog = encoding.base64.b64decode(approval_b64)
    clearstate_prog = encoding.base64.b64decode(clearstate_b64)

    # Create a transaction to deploy the contract
    # Obtain the current network suggested parameters.
    sp = client.suggested_params()
    sp.flat_fee = True
    sp.fee = 1000
    # Create an application call transaction without an application ID (aka Create)
    txn = future.transaction.ApplicationCreateTxn(
        bank_address,
        sp,
        future.transaction.OnComplete.NoOpOC,
        approval_prog,
        clearstate_prog,
        future.transaction.StateSchema(0, 0),
        future.transaction.StateSchema(0, 0),
        app_args=app_args
    )

    # launch contract on chain
    txid = client.send_transaction(txn.sign(bank_key))
    future.transaction.wait_for_confirmation(client, txid)
    response = client.pending_transaction_info(txid)

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

    client.send_transactions([signedPayTxn, signedAppCallTxn])

    future.transaction.wait_for_confirmation(client, appCallTxn.get_txid())

    return appID, appAddr


def pay2contract(origin, target, amount, origin_key, client, appID):

    sp = client.suggested_params()
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

    client.send_transactions([signedPayTxn, signedAppCallTxn])

    future.transaction.wait_for_confirmation(client, appCallTxn.get_txid())

