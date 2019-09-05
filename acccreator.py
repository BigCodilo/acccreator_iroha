import csv
import binascii
import os
import random
import string
import threading
import time

from iroha import IrohaCrypto
from iroha import Iroha, IrohaGrpc



class User:
    Name = ""
    Pubkey = ""
    PrivKey = ""


users = list()

class AccCreator:
    def __init__(self):

        # self.IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', '192.168.88.202')
        self.IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', 'localhost')
        self.IROHA_PORT = os.getenv('IROHA_PORT', '50051')
        self.admin_private_key = 'f101537e319568c765b2cc89698325604991dca57b9716b58016b253506cab70'
        self.iroha = Iroha('admin@test')
        self.net = IrohaGrpc('{}:{}'.format(self.IROHA_HOST_ADDR, self.IROHA_PORT))
        self.txAmount = 0
        self.CreateDomainAsset()
        self.AddAdminCoin()

    def Starting(self, accsByThread):
        # self.CreateDomainAsset()
        # self.AddAdminCoin()
        # start_time = time.time()
        self.CreateManyAccs(accsByThread)
        self.SendToAllAccs()

    def SendTxAndPrintstatus(self, transaction):
        hex_hash = binascii.hexlify(IrohaCrypto.hash(transaction))
        print('Transaction hash = {}, creator = {}'.format(
            hex_hash, transaction.payload.reduced_payload.creator_account_id))
        self.net.send_tx(transaction)
        self.txAmount += 1
        # for status in self.net.tx_status_stream(transaction):
        #     print(status)


    def CreateDomainAsset(self):
        commands = [
            self.iroha.command('CreateDomain', domain_id='domain', default_role='user'),
            self.iroha.command('CreateAsset', asset_name='coin',
                          domain_id='domain', precision=2)
        ]
        tx = IrohaCrypto.sign_transaction(
            self.iroha.transaction(commands), self.admin_private_key)
        self.SendTxAndPrintstatus(tx)


    #______________________________________________CREATINGUSER____________________________


    def CreateAccount(self, accName):
        user = User()
        user.Name = accName + "@" + "domain"
        user.PrivKey = IrohaCrypto.private_key()
        user.PubKey = IrohaCrypto.derive_public_key(user.PrivKey)
        tx = self.iroha.transaction([
            self.iroha.command('CreateAccount', account_name=accName, domain_id='domain',
                          public_key=user.PubKey)
        ])
        IrohaCrypto.sign_transaction(tx, self.admin_private_key)
        self.SendTxAndPrintstatus(tx)
        users.append(user)

    def RandomName(self, stringLength=10):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(stringLength))

    def CreateManyAccs(self, amount):
        for i in range(1, amount):
            name = self.RandomName()
            self.CreateAccount(name)

    def SaveAccsToCSV(self):
        outfile = open('accounts.csv','w')
        writer = csv.writer(outfile)
        writer.writerow(["NAME", "PUBLIC_KEY", "PRIVATE_KEY"])
        for v in users:
            writer.writerow([v.Name, v.PubKey, v.PrivKey])

        outfile.close()


    #ADDIINGCOIN

    def AddAdminCoin(self):
        tx = self.iroha.transaction([
            self.iroha.command('AddAssetQuantity',
                          asset_id='coin#domain', amount='1000000000.00')
        ])
        IrohaCrypto.sign_transaction(tx, self.admin_private_key)
        self.SendTxAndPrintstatus(tx)

    #___________TRANSFERING COINS_________________________

    def SendToAllAccs(self):
        for user in users:
            self.SendToUser(user)

    def SendToUser(self, user):
        tx = self.iroha.transaction([
            self.iroha.command('TransferAsset', src_account_id='admin@test', dest_account_id=user.Name,
                          asset_id='coin#domain', description='init top up', amount='100.00')
        ])
        IrohaCrypto.sign_transaction(tx, self.admin_private_key)
        self.SendTxAndPrintstatus(tx)

#STARTER____________________________________________________

def main():
    threadsAmount = input("Amount of threads: ")
    accountsAmount = input("Amount of accounts: ")
    accsByThread = int(accountsAmount)/int(threadsAmount)

    startTime = time.time()

    accCreator = AccCreator()
    for i in range(0, int(threadsAmount)):
        threading.Thread(target=accCreator.Starting, args = [int(accsByThread)]).start()
        # accCreator.Starting()

    while threading.activeCount() > 1:
        time.sleep(1);

    totalTime = startTime - time.time()

    accCreator.SaveAccsToCSV()
    print("Accounts created: ", accountsAmount)
    print("Threads: ", threadsAmount)
    print("For: ", totalTime, " seconds")
    print("Total transactions: ", accCreator.txAmount)




if __name__ == "__main__":
    main()