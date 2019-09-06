import binascii
import csv
import os
import threading

from iroha import IrohaCrypto
from iroha import Iroha, IrohaGrpc
import time


class User:
    Name = ""
    PubKey = ""
    PrivKey = ""


users = list()
transactions = list()
irohaTests = list()
success_txs = 0
txsStatus = list()


class TestIroha:
    def __init__(self, user, port="50051", host="localhost"):
        self.IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', '192.168.88.202') #andrey
        # self.IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', '192.168.88.62') #sergey
        # self.IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', host)
        self.IROHA_PORT = os.getenv('IROHA_PORT', port)
        self.admin_private_key = 'f101537e319568c765b2cc89698325604991dca57b9716b58016b253506cab70'
        self.iroha = Iroha(user.Name)
        self.net = IrohaGrpc('{}:{}'.format(self.IROHA_HOST_ADDR, self.IROHA_PORT), 1000)

    def SendTx(self, transaction):
        hex_hash = binascii.hexlify(IrohaCrypto.hash(transaction))
        print('Transaction hash = {}, creator = {}'.format(
            hex_hash, transaction.payload.reduced_payload.creator_account_id))
        self.net.send_tx(transaction)
        exit_status = list()
        # for status in self.net.tx_status_stream(transaction):
        #     print(status)
        return exit_status

    def SignTx(self, from_user, to_user):
        tx = self.iroha.transaction([
            self.iroha.command('TransferAsset', src_account_id=from_user.Name, dest_account_id=to_user.Name,
                               asset_id='coin#domain', description='sending', amount='0.01')
        ])
        IrohaCrypto.sign_transaction(tx, from_user.PrivKey)
        transactions.append(tx)

    def GetTxsStatus(self):
        txsChecked = 0
        print("Starting checking")
        for transaction in transactions:
            txsChecked += 1
            for status in self.net.tx_status_stream(transaction):
                txsStatus.append(status)
            if txsChecked%10 == 0:
                print(txsChecked, " transaction checked")


def ReadCSV():
    global users
    with open("accounts.csv", "r", newline="") as file:
        reader = csv.reader(file)
        first_line = True
        for row in reader:
            if first_line:
                first_line = False
                continue
            user = User()
            user.Name = row[0]
            user.PubKey = row[1][2:len(user.PubKey) - 1]
            user.PrivKey = row[2][2:len(user.PrivKey) - 1]
            users.append(user)

# ttwo threads

def FirstHalf():
    irohaSender = TestIroha(users[1])
    for tx in transactions[0:int(len(transactions)/2)]:
        irohaSender.SendTx(tx)
        global success_txs
        success_txs += 1

def SecondHalf():
    irohaSender = TestIroha(users[2])
    for tx in transactions[int(len(transactions) / 2):int(len(transactions))]:
        irohaSender.SendTx(tx)
        global success_txs
        success_txs += 1

#   end of threading

def main():
    ReadCSV()
    amount_tx = 0
    users_length = len(users)
    for from_user in users[0:int(users_length/ 2)]:
        iroha_test = TestIroha(from_user)
        irohaTests.append(iroha_test)
        for to_user in users[int(users_length/ 2):users_length]:
            print(" from " + from_user.Name + " to " + to_user.Name)
            iroha_test.SignTx(from_user, to_user)
            amount_tx += 1


    startTime = time.time()

    t1 = threading.Thread(target=FirstHalf)
    t2 = threading.Thread(target=SecondHalf)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    endTime = startTime - time.time()
    # for iroha_test in irohaTests:
    #     for tx in transactions[start:end]:
    #         status = iroha_test.SendTx(tx)
    #         print(status)
    #         success_txs += 1
    #     start = end
    #     end += txs_per_account

    print("All threads closed")
    time.sleep(5)
    txStatusObj = TestIroha(users[1])
    txStatusObj.GetTxsStatus()

    successesTxs = 0
    for txStatus in txsStatus:
        if txStatus[0] == "COMMITTED":
            successesTxs += 1


    print("Total time: ", endTime)
    print("Total txs: ", success_txs)
    print("Seccesses txs: ", successesTxs)


if __name__ == "__main__":
    main()
