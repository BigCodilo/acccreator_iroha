import csv
import binascii
import os
import random
import string
import time
from threading import Thread

from iroha import IrohaCrypto
from iroha import Iroha, IrohaGrpc



class User:
    Name = ""
    Pubkey = ""
    PrivKey = ""


class AccCreator:
    def __init__(self):

        # self.IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', '192.168.88.202')
        self.IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', 'localhost')
        self.IROHA_PORT = os.getenv('IROHA_PORT', '50051')
        self.admin_private_key = 'f101537e319568c765b2cc89698325604991dca57b9716b58016b253506cab70'
        self.iroha = Iroha('admin@test')
        self.net = IrohaGrpc('{}:{}'.format(self.IROHA_HOST_ADDR, self.IROHA_PORT))
        self.users = list()

    def Starting(self):
        self.CreateDomainAsset()
        self.AddAdminCoin()
        # start_time = time.time()
        self.CreateManyAccs(30)
        self.SendToAllAccs()

    def SendTxAndPrintstatus(self, transaction):
        hex_hash = binascii.hexlify(IrohaCrypto.hash(transaction))
        print('Transaction hash = {}, creator = {}'.format(
            hex_hash, transaction.payload.reduced_payload.creator_account_id))
        self.net.send_tx(transaction)
        for status in self.net.tx_status_stream(transaction):
            print(status)


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
        self.users.append(user)

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
        for v in self.users:
            writer.writerow([v.Name, v.PubKey, v.PrivKey])

        outfile.close()


    #ADDIINGCOIN

    def AddAdminCoin(self):
        tx = self.iroha.transaction([
            self.iroha.command('AddAssetQuantity',
                          asset_id='coin#domain', amount='100000.00')
        ])
        IrohaCrypto.sign_transaction(tx, self.admin_private_key)
        self.SendTxAndPrintstatus(tx)

    #___________TRANSFERING COINS_________________________

    def SendToAllAccs(self):
        for user in self.users:
            self.SendToUser(user)

    def SendToUser(self, user):
        tx = self.iroha.transaction([
            self.iroha.command('TransferAsset', src_account_id='admin@test', dest_account_id=user.Name,
                          asset_id='coin#domain', description='init top up', amount='10.00')
        ])
        print("sended")
        IrohaCrypto.sign_transaction(tx, self.admin_private_key)
        self.SendTxAndPrintstatus(tx)

#STARTER____________________________________________________

def main():
    accCreator = AccCreator()
    accCreator.Starting()


    # accCreator.CreateDomainAsset()
    # accCreator.AddAdminCoin()
    # start_time = time.time()
    # accCreator.CreateManyAccs(int(input("amount of accounts: ")))
    # accCreator.SendToAllAccs()
    # print("--- %s seconds ---" % (time.time() - start_time))
    # accCreator.SaveAccsToCSV()
    # print("done")


if __name__ == "__main__":
    main()