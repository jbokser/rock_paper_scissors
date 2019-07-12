#!/usr/bin/env python3

from json            import loads, load, dumps, dump
from web3            import Web3, HTTPProvider, eth
from web3.exceptions import InvalidAddress, ValidationError
from web3.exceptions import BadFunctionCallOutput
from tabulate        import tabulate
from click_shell     import shell
from os.path         import isfile, getsize, splitext
from eth_account     import Account
from time            import sleep
from types           import SimpleNamespace
from web3.exceptions import InvalidAddress, ValidationError
from web3.exceptions import BadFunctionCallOutput
import click, base64, hashlib, datetime, functools



json_file = '.'.join([splitext(__file__)[0], 'json'])



def raw_encode(key, clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()



def raw_decode(key, enc):
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)



def hash_(value):
    return hashlib.sha256(str(value).encode('utf-8')).hexdigest()



def encode(key, clear):
    raw = '{}{}'.format(hash_(clear), str(clear))
    return raw_encode(hash_(key), raw)



def decode(key, enc):
    try:
        raw = raw_decode(hash_(key), enc)
        value, test_hash = raw[64:], raw[:64]
    except:
        raise ValueError
    if hash_(value) != test_hash:
        raise ValueError
    return value



class PersistentDict(dict):

    def __init__(self, filename, *args, **kwargs):
        self.filename = filename
        self._load();
        self.update(*args, **kwargs)

    def _load(self):
        if isfile(self.filename) and getsize(self.filename) > 0:
            with open(self.filename, 'r') as file_:
                self.update(load(file_))

    def _dump(self):
        with open(self.filename, 'w') as file_:
            dump(self, file_, indent=2, sort_keys=True)

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)
        self._dump()

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._dump()

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items():
            self[key] = value
        self._dump()



conf = PersistentDict(json_file)

class BadPassword(Exception):
    pass

class Wallet(dict):

    def __init__(self, storage, main_key='wallet'):
        if not main_key in storage:
            storage[main_key] = {'default': None, 'addresses': {}}
        self._storage  = storage
        self._main_key = main_key
        self.password  = None
        self._default  = storage[main_key]['default']
        for key, value in dict(storage[main_key]['addresses']).items():
            dict.__setitem__(self, key, value)

    def _dump(self):
        self._storage[self._main_key] = {'default':   self._default,
                                         'addresses': dict(self)}

    def _get_password(self, key, confirmation=False):
        if self.password:
            pwd = self.password
            self.password = None
        else:
            pwd = click.prompt(
                'Enter private key password for {}'.format(key),
                type = str,
                hide_input = True,
                confirmation_prompt = confirmation)
        return pwd

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        try:
            value = decode(self._get_password(key), value)
        except ValueError:
            raise BadPassword
        return value

    def __setitem__(self, key, value):
        value     = str(value)
        key       = str(Web3.toChecksumAddress(str(key)))
        valid_key = str(Account.privateKeyToAccount(value).address)
        if valid_key != key:
            raise ValueError
        dict.__setitem__(self, key, encode(self._get_password(key,
            confirmation=True), value))
        if len(self)==1:
            self._default = key
        self._dump()

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        if key == self._default:
            self._default = None
        if len(self)==1:
            self._default = self.addresses[0]
        self._dump()

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    @property
    def addresses(self):
        return list(dict.keys(self))

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, value):
        value = str(Web3.toChecksumAddress(str(value)))
        if value in self:
            self._default = value
            self._dump()
        else:
            raise ValueError('Address not in wallet')

    def add_priv_key(self, value):
        value   = str(value)
        address = str(Account.privateKeyToAccount(value).address)
        self[address] = value
        return address



wallet = Wallet(conf)



class Main():



    def __init__(self, uri):
        self._uri = uri
        self.web3 = Web3(HTTPProvider(uri))
        self.contracts = SimpleNamespace()
        for c in conf['contracts']:
            if conf['contracts'][c]['enable']:
                addr = Web3.toChecksumAddress(conf['contracts'][c]['address'])
                abi  = conf['contracts'][c]['abi']
                name = conf['contracts'][c]['name']
                obj  = self.web3.eth.contract(address = addr, abi = abi)
                setattr(obj, 'name', name)
                setattr(self.contracts, c, obj)



    @property
    def uri(self):
        """ Devuelve donde se conecta """
        return self._uri



    @property
    def is_connected(self):
        """ Devuelve si esta conectado """
        return self.web3.isConnected()



    @property
    def gas_price(self):
        """ Precio del gas """
        return self.web3.eth.gasPrice



    @property
    def block_number(self):
        """ Numero del ultimo blocque """
        return self.web3.eth.blockNumber



    def balance(self, address):
        """ Obtiene el balance de un address """
        return self.web3.eth.getBalance(address)



    def get_transaction_receipt(self, transaction_hash):
        """ Obtiene datos de una transaccion """
        return self.web3.eth.getTransactionReceipt(transaction_hash)



    def tranfer(self, private_key, to_address, value, unit='wei'):
        """ Tranferencia """


        from_address = Account.privateKeyToAccount(private_key).address

        from_address = Web3.toChecksumAddress(from_address)
        to_address   = Web3.toChecksumAddress(to_address)

        value = self.web3.toWei(value, unit)

        nonce = self.web3.eth.getTransactionCount(from_address)

        transaction = dict(chainId  = conf['node']['chain_id'],
                           nonce    = nonce,
                           gasPrice = self.gas_price,
                           gas      = 100000,
                           to       = to_address,
                           value    = value)

        signed_transaction = self.web3.eth.account.signTransaction(transaction,
            private_key)

        return self.web3.eth.sendRawTransaction(
            signed_transaction.rawTransaction)



    def transaction(self, fnc, private_key, value=0, gas_limit=0):

        if not gas_limit:
            gas_limit = fnc.estimateGas()

        from_address = Account.privateKeyToAccount(private_key).address
        from_address = Web3.toChecksumAddress(from_address)

        nonce = self.web3.eth.getTransactionCount(from_address)

        transaction_dict = dict(chainId  = conf['node']['chain_id'],
                                nonce    = nonce,
                                gasPrice = self.gas_price,
                                gas      = gas_limit,
                                value    = value)

        transaction = fnc.buildTransaction(transaction_dict)

        signed = self.web3.eth.account.signTransaction(transaction,
                                                       private_key = private_key)

        transaction_hash = self.web3.eth.sendRawTransaction(
            signed.rawTransaction)

        return transaction_hash.hex()



main = Main(conf['node']['uri'])



def wei_to_tuple(value):
    """ wei --> (value, str_unit) """
    value    = int(value)
    str_unit = 'wei'
    if value > 1000:
        for str_unit in ['Kwei', 'Mwei', 'Gwei', 'Microether', 'Milliether',
                         'Ether', 'Kether', 'Mether', 'Gether', 'Tether']:
            value = value/1000
            if value<1000:
                break
    return (value, str_unit)



def wei_to_str(value):
    """ wei --> str """
    return '{0:.2f} {1}'.format(*wei_to_tuple(value))



def default_address():
    """ Devuelve la cuenta por defecto, si no hay, mensaje """
    if wallet.default:
        return wallet.default
    else:
        print(white('Debe configurar una dirección por defecto para operar'))
        if len(wallet):
            print(white("Ver el comando 'wallet default ADDRESS'"))
        else:
            print(white("Ver el comando 'wallet add PRIVATE_KEY'"))
        return None



# Funciones para colorear
yellow = lambda x: click.style(str(x), fg='bright_yellow')
white  = lambda x: click.style(str(x), fg='bright_white')
red    = lambda x: click.style(str(x), fg='bright_red')
green  = lambda x: click.style(str(x), fg='bright_green')



def intro():
    print(white("Simple Smart Contract Shell\nBy"),
          red('Juan S. Bokser <juan.bokser@gmail.com>'),
          '\n')



def validate_is_connect(fnc):
    """ Decorador para validar que uno este conectado """

    @functools.wraps(fnc)
    def wrapper():
        if not main.is_connected:
            raise click.ClickException(red(
                'Can not connect to the node\n{}'.format(main.uri)))
        return fnc()

    return wrapper



@shell(prompt = yellow('>>> '))
def app():

    intro()

    for c in main.contracts.__dict__.values():
        print(white('Contract {}\n{}\n{}\n').format(
            white(repr(c.name)),
            yellow(c.address),
            white(wei_to_str(main.balance(c.address)) if main.is_connected
                                                      else '')))

    address = default_address()

    if address:
        print(white('Default address\n{}\n{}\n').format(
            yellow(address),
            white(wei_to_str(main.balance(address)) if main.is_connected
                                                    else '')))
    else:
        print()

    if not main.is_connected:
        print(red('Can not connect to the node\n{}'.format(main.uri)))
        print()

    print(white("Usar el comando 'help' para mas informacion"))



app.shell.ruler        = ''
app.shell.doc_header   = white('Comandos disponibles:')
app.shell.undoc_header = white('Ayuda y salida:')



@app.group(name='blockchain')
@validate_is_connect
def blockchain():
    """ Referido a la blockchain """



@blockchain.command(name='gas-price')
def blockchain_gas_price():
    """ Muestra el precio actual del Gas """
    print(white('gasPrice = {}').format(wei_to_str(main.gas_price)))



@blockchain.command(name='block-number')
def blockchain_block_number():
    """ Último numero de bloque """
    print(white('blockNumber = {}').format(main.block_number))



@blockchain.command(name='get-balance')
@click.argument('address')
def blockchain_get_balance(address):
    """ Muestra el balance de ADDRESS """

    try:
        address = str(Web3.toChecksumAddress(str(address)))
    except ValueError as e:
        raise click.BadParameter(red(e))

    print(white('{} = {}').format(
        address,
        wei_to_str(main.balance(address))))



@app.group(name='wallet')
def accounts():
    """ Referido a los Address para operar """



@accounts.command(name='del')
@click.argument('address')
def accounts_del(address):
    """ Borra a ADDRESS de la Wallet """

    try:
        address = str(Web3.toChecksumAddress(str(address)))
    except ValueError as e:
        raise click.BadParameter(red(e))

    if address not in wallet:
        raise click.BadParameter(red('Address not found'))

    del wallet[address]



@accounts.command(name='add')
@click.argument('private_key')
def acounts_add(private_key):
    """ Agrega un address a la Wallet con la PRIVATE_KEY de la misma """
    try:
        address = wallet.add_priv_key(private_key)
    except ValueError as e:
        raise click.BadParameter(red(e))
    print(white('{} has been added.'.format(address)))



@accounts.command(name='default')
@click.argument('address')
def acounts_default(address):
    """ Asigna el ADDRESS por defecto para operar """
    try:
        address = str(Web3.toChecksumAddress(str(address)))
        wallet.default = address
    except ValueError as e:
        raise click.BadParameter(red(e))
    print(white('{} has been marked as default.'.format(address)))



@accounts.command(name='list')
def accounts_list():
    """ Listado de las addresses de la Wallet """
    if not wallet:
        print(white('\n'.join(['', '(none)', ''])))
        return
    table = [ list( wei_to_tuple(main.balance(a)) if main.is_connected
                                                  else '?' ) +
              [ 'Yes' if wallet.default == a else 'No'] +
              [ yellow(a) if wallet.default == a else a]
             for a in wallet.addresses ]
    table.sort(reverse = True)
    print('\n'.join(['',
                     tabulate(table, headers=[white('Balance'),
                                              white('Unit'),
                                              white('Default'),
                                              white('Address')]),
                     '']))



@accounts.command(name='balance')
@validate_is_connect
def accounts_balance():
    """ Muestra el balance de la direccion por defecto """
    if wallet.default:
        print(white('{}').format(wei_to_str(main.balance(wallet.default))))
    else:
        print(white('Debe configurar una dirección por defecto para operar'))
        if len(wallet):
            print(white("Ver el comando 'wallet default ADDRESS'"))
        else:
            print(white("Ver el comando 'wallet add PRIVATE_KEY'"))



def show_transaction(transaction):
    """
    Muestra datos de una transaccion

    Espera que el bloque se mine si es necesario.
    """
    print()
    print(' '.join([white('Transaction:'), yellow(transaction)]))

    print()
    print('Getting block ...', end='', flush=True)
    transaction_receipt, c = None, 1
    while transaction_receipt is None and (c < 120):
        transaction_receipt = main.get_transaction_receipt(transaction)
        print('.', end='', flush=True)
        c += 1
        if not transaction_receipt:
            sleep(2.5)
    if transaction_receipt is None:
        print(red(' Timeout!'))
    else:
        print(white(' Ok!'))
        print('')
        print('Block Number: {}'.format(
            white(transaction_receipt.blockNumber)))
        print('Gas used:     {}'.format(
            white(wei_to_str(transaction_receipt.gasUsed))))
        print('Status:       {}'.format(
            {0: red('Fail'),
             1: green('Ok')}.get(
                transaction_receipt.status,
                white(transaction_receipt.status))))
    print('')
    return transaction_receipt



units = ['wei', 'kwei', 'mwei', 'gwei', 'nanoether', 'microether',
         'milliether', 'ether']



@accounts.command(name='tranfer')
@click.argument('to_address')
@click.argument('value', type=int)
@click.argument('unit', default='wei', type=click.Choice(units))
@validate_is_connect
def acounts_tranfer(to_address, value, unit = 'wei'):
    """
    Transfiere VALUE [UNIT] de la cuenta por defecto a TO_ADDRESS

    Por defecto UNIT es wei
    """

    from_address = default_address()

    if not from_address:
        return

    try:
        to_address = str(Web3.toChecksumAddress(str(to_address)))
    except ValueError as e:
        raise click.BadParameter(red(e))

    try:
        transaction = main.tranfer(private_key = wallet[from_address],
                                   to_address  = to_address,
                                   value       = value,
                                   unit        = unit).hex()
    except BadPassword:
        raise click.ClickException(red('Bad private key password'))

    show_transaction(transaction)



def show_transaction_move_index(transaction):
    """
     Muestra la transaccion de una jugada

    Igual que show_transaction(transaction) pero tambien mustra el index de
    la jugada
    """
    receipt  = show_transaction(transaction)
    contract = main.contracts.rps
    event    = contract.events.MakeAmove()
    events   = event.processReceipt(receipt)
    for e in events:
        print('Move index:   {}'.format(white(e.args._index)))
    if events:
        print()



@app.group(name='play')
@validate_is_connect
def play():
    """ Referido al juego de RockPaperScissors """



@play.command(name='bet')
def play_bet():
    """ Muestra la apuesta por jugada """
    contract = main.contracts.rps
    bet      = contract.functions.bet().call()
    print(white('bet = {}').format(wei_to_str(bet)))



@play.command(name='prize')
def play_prize():
    """ Muestra el premio por jugada ganada"""
    contract = main.contracts.rps
    prize    = contract.functions.prize().call()
    print(white('prize = {}').format(wei_to_str(prize)))



class ResultClass():
    """ Enum de los posibles resultados """

    def __init__(self):
        e = 'lose tie win bad wait opponent_not_showed not_showed'
        e = list(zip(range(len(e.split())), e.split()))
        self.revert = dict(e)
        self.names = dict(e)
        for value, key in e:
            setattr(self, key, value)



Result = ResultClass()



Result.names[Result.lose]                = 'Perdio'
Result.names[Result.tie]                 = 'Empato'
Result.names[Result.win]                 = 'Gano'
Result.names[Result.bad]                 = 'Jugada inexistente'
Result.names[Result.wait]                = 'Esperando oponente'
Result.names[Result.opponent_not_showed] = 'Jugada de oponente aun no mostrada'
Result.names[Result.not_showed]          = 'Jugada aun no mostrada'



class MoveTypeClass():
    """ Enum de las posibles jugadas """

    def __init__(self):
        e = 'rock paper scissors expired'
        e = list(zip(range(len(e.split())), e.split()))
        self.revert = dict(e)
        self.names = dict(e)
        for value, key in e:
            setattr(self, key, value)



MoveType = MoveTypeClass()



MoveType.names[MoveType.rock]     = 'Piedra'
MoveType.names[MoveType.paper]    = 'Papel'
MoveType.names[MoveType.scissors] = 'Tijera'
MoveType.names[MoveType.expired]  = '(expirado)'



@play.command(name='info')
@click.argument('index', type=int)
def play_see_a_move(index):
    """ Muestra el informacion de la jugada con indice INDEX """

    contract = main.contracts.rps

    result_code = contract.functions.seeAmove(index).call()
    result = Result.names[result_code]

    if result_code == Result.bad:
        print(white(result))
        return

    timestamp, hash_, addr, move_type = \
        contract.functions.moves(index).call()

    timestamp = datetime.datetime.fromtimestamp(timestamp)

    str_timestamp = ''.join(
        [str(timestamp),
         ' (',
         str(datetime.datetime.now()-timestamp).split('.')[0],
         ')'])

    print()
    print('Timestamp: {}'.format(white(str_timestamp)))
    print('Index:     {}'.format(white(index)))
    print('Hash:      {}'.format(white(hash_.hex())))
    if not result_code in [Result.not_showed,
                           Result.wait]:
        if move_type != MoveType.expired and \
                addr!='0x0000000000000000000000000000000000000000':
            print('Addres:    {}'.format(white(addr)))
        if addr != '0x0000000000000000000000000000000000000000':
            print('Jugada:    {}'.format(white(MoveType.names[move_type])))
    if result_code==Result.opponent_not_showed and \
            addr == '0x0000000000000000000000000000000000000000':
        print('Resultado: {}'.format(white(
            'Jugada de oponente y propia aun no mostradas')))
    else:
        print('Resultado: {}'.format(white(result)))
    print()



move_type_choice = {'r':0, 'p':1, 's':2}

@play.command(name='make')
@click.argument('move_type', type=click.Choice(move_type_choice))
@click.argument('secret')
def play_make_a_move(move_type, secret):
    """
    Hace una jugada del tipo (r), (p) o (s) escondiendo la misma con SECRET

    (r) es Piedra

    (p) es Papel

    (s) es Tijera

    SECRET sera necesario para revelar la juagada frente al oponente
    """

    from_address = default_address()
    move_type    = move_type_choice[move_type]

    if not from_address:
        return

    contract     = main.contracts.rps
    makeMoveHash = contract.functions.makeMoveHash
    makeAmove    = contract.functions.makeAmove

    bet = contract.functions.bet().call()

    move_hash = makeMoveHash(_nonce = secret,
                             _type  = move_type).call().hex()

    try:
        transaction = main.transaction(fnc         = makeAmove(move_hash),
                                       private_key = wallet[from_address],
                                       gas_limit   = 700000,
                                       value       = bet)

    except BadPassword:
        raise click.ClickException(red('Bad private key password'))

    show_transaction_move_index(transaction)



@play.command(name='show')
@click.argument('index', type=int)
@click.argument('secret')
def play_show_a_move(index, secret):
    """ Revela una jugada de indice INDEX con SECRET """

    from_address = default_address()

    if not from_address:
        return

    contract    = main.contracts.rps
    showMyMove  = contract.functions.showMyMove

    try:
        transaction = main.transaction(fnc         = showMyMove(index, secret),
                                       private_key = wallet[from_address],
                                       gas_limit   = 700000)

    except BadPassword:
        raise click.ClickException(red('Bad private key password'))

    show_transaction(transaction)



@play.command(name='claim')
@click.argument('index', type=int)
def play_claim_a_expired_move(index):
    """ Reclama una jugada expirada del oponente a la jugada INDEX """

    from_address = default_address()

    if not from_address:
        return

    contract           = main.contracts.rps
    claimAnExpiredMove = contract.functions.claimAnExpiredMove

    try:
        transaction = main.transaction(fnc         = claimAnExpiredMove(index),
                                       private_key = wallet[from_address],
                                       gas_limit   = 700000)

    except BadPassword:
        raise click.ClickException(red('Bad private key password'))

    show_transaction(transaction)



@play.command(name='timeout')
def play_timeout():
    """ Muestra el timeout por jugada """
    contract = main.contracts.rps
    print(white('Timeout = {}').format(
        white(datetime.timedelta(
            seconds = contract.functions.moveTimeOut().call()))))



@app.group(name='owner')
@validate_is_connect
def owner():
    """ Referido al dueño del contrato 'RockPaperScissors' """



@owner.command(name='who')
def owner_who():
    """ Muestra el Owner """
    contract = main.contracts.rps
    owner    = contract.functions.owner().call()
    print(white('Owner = {}').format(owner))



@owner.command(name='funds')
def owner_funds():
    """ Muestra las comisiones disponibles para retirar """
    contract = main.contracts.rps
    value    = contract.functions.ownerCollect().call()
    print(white('Value = {}').format(wei_to_str(value)))



@owner.command(name='collect')
def owner_collect():
    """ Transfiere las comisones al Owner """

    contract = main.contracts.rps
    value    = contract.functions.ownerCollect().call()
    owner    = contract.functions.owner().call()

    from_address = default_address()

    if not from_address:
        return

    if value <= 0:
        raise click.ClickException(red('No funds available'))

    if owner != from_address:
        raise click.ClickException(red('You are not the owner'))

    collect = contract.functions.collect

    try:
        transaction = main.transaction(fnc         = collect(),
                                       private_key = wallet[from_address],
                                       gas_limit   = 700000)

    except BadPassword:
        raise click.ClickException(red('Bad private key password'))

    show_transaction(transaction)



@click.command()
@click.option('--clean-up', is_flag=True, help='Remove all private keys')
def start_up(clean_up):
    """ Simple Smart Contract Shell By Juan S. Bokser <juan.bokser@gmail.com>
    """
    if clean_up:
        intro()
        print(yellow('//// REMOVING ALL PRIVATE KEYS ////'))
        print()
        if click.confirm(white('Do you want to continue?')):
            conf['wallet'] = {'default': None, 'addresses': {}}
            print()
            print(white('Done!'))
            print()
        else:
            print()
            print(white('Abort!'))
            print()
    else:
        app()



if __name__ == '__main__':
    start_up()


