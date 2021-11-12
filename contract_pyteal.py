from pyteal import *
import os

def approval_program():

    # don't need any real fancy initialization
    handle_creation = Seq([
        Return(Int(1))
    ])

    # initialize scratch variables
    # total amounts to make sure that the contract
    # receives at least as much as is sent out + fees
    totalAmountRec = ScratchVar(TealType.uint64) 
    totalAmountSent = ScratchVar(TealType.uint64)
    # i for the for loop
    i = ScratchVar(TealType.uint64) 

    # for each arg send a transaction of that amount
    # to the corresponding account in the accounts array
    send_inner_txns = Seq(
        For(i.store(Int(0)), i.load() < Txn.application_args.length(), i.store(i.load() + Int(1))).Do(
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields({
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.receiver: Txn.accounts[i.load() + Int(1)],
                    TxnField.amount: Btoi(Txn.application_args[i.load()]),
                }),
                InnerTxnBuilder.Submit()
        )),
        Int(1)
    )

    # make sure that the contract receives at least as much as the 
    # amount it sends out + fees, and that each transaction sends
    # the algos to the contract's address
    check_valid = Seq(
        totalAmountRec.store(Int(0)),
        totalAmountSent.store(Int(0)),

        For(i.store(Int(0)), i.load() < Global.group_size() - Int(1), i.store(i.load() + Int(1))).Do(Seq(
            totalAmountRec.store(totalAmountRec.load() + Gtxn[i.load()].amount()),
            If(Gtxn[i.load()].receiver() != Global.current_application_address(), Return(Int(0))))),

        For(i.store(Int(0)), i.load() < Txn.application_args.length(), i.store(i.load() + Int(1))).Do(Seq(
            totalAmountSent.store(totalAmountSent.load() + Btoi(Txn.application_args[i.load()])))),

        totalAmountRec.load() >= totalAmountSent.load() + Global.min_txn_fee() * Txn.application_args.length(),
        )
    
    handle_noop = And(
        check_valid,
        Txn.accounts.length() == Txn.application_args.length(), # make sure each amount has an account to send to
        Txn.accounts.length() <= Int(16), # contracts can send max 16 innerTxns
        send_inner_txns
    )

    # doesn't need anyone to opt in
    handle_optin = Return(Int(0))

    # only the creator can closeout the contract
    handle_closeout = Return(Txn.sender() == Global.creator_address())

    # nobody can update the contract
    handle_updateapp = Return(Int(0))

    # only creator can delete the contract
    handle_deleteapp = Return(Txn.sender() == Global.creator_address())


    # handle the types of application calls
    program = Cond(
        [Txn.application_id() == Int(0), handle_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
        [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp],
        [Txn.on_completion() == OnComplete.NoOp, Return(handle_noop)]
    )
    return compileTeal(program, mode=Mode.Application, version=5)

# let clear state happen
def clear_state_program():
    program = Return(Int(1))
    return compileTeal(program, mode=Mode.Application, version=5)

# compile to teal and write to file
if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(path,"approval.teal"), "w") as f:
        f.write(approval_program())

    with open(os.path.join(path,"clear.teal"), "w") as f:
        f.write(clear_state_program())