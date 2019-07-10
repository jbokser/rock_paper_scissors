pragma solidity ^0.5.9;
// RockPaperScissors por Juan S. Bokser <juan.bokser@gmail.com>
// Para mas informacion https://tinyurl.com/y3pjfxha


// Contrato que maneja dueño
// Para ser usado como herencia de otros contratos
contract Owned {

    address payable public owner;

    constructor() public {
        owner = msg.sender;
    }

    function isOwner(address _addr) internal view returns(bool) {
        return (_addr == owner);
    }

    function senderIsOwner() internal view returns(bool) {
        return (isOwner(msg.sender));
    }

    modifier onlyOwner {
        require(senderIsOwner(), 'Unauthorized!');
        _;
    }

}



// Contrato que maneja dueño con transfetencia de pertenencia
// Para ser usado como herencia de otros contratos
contract TransferableOwned is Owned {

    address payable public newOwner;

    event OwnershipTransferred(address indexed _from, address indexed _to);

    function transferOwnership(address payable _newOwner) public onlyOwner {
        newOwner = _newOwner;
    }

    function acceptOwnership() public {
        require(msg.sender == newOwner);
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
        newOwner = address(0);
    }

}



contract RockPaperScissors is TransferableOwned{

    // Enum con las jugadas posibles
    enum MoveType {rock, paper, scissors, expired}

    // Enum con los resultados posibles
    enum Result {lose, tie, win, bad, wait, opponent_not_showed, not_showed}

    // Estructura con los datos de cada jugada
    struct Move {
        uint timestamp;
        bytes32 hash;
        address payable addr;
        MoveType _type;
    }

    // Array con cada jugada...
    // Donde las jugadas con indice par tienen como oponenete
    // las jugada anterior con indice impar
    Move[] public moves;

    // Apuesta de entrada para hacer una jugada
    uint public bet;

    // Premio para el ganador
    uint public prize;

    // Comisiones ganadas para el dueños
    uint public ownerCollect;

    // Tiempo de expiracion de una jugada
    uint public moveTimeOut;

    // Evento de una nueva jugada
    event MakeAmove(address indexed _addr, uint _index);


    // Inicio las variables
    constructor() public {
        bet         = 10 finney;
        prize       = 19 finney; // 10% para la casa
        moveTimeOut = 10 minutes;
    }



    // Funcion a para armar un hash de una jugada
    function makeMoveHash(string memory _nonce, // Nonce necesario 
                          MoveType _type        // Jugada
                          ) public pure returns (bytes32 _hash) {
         require(_type!=MoveType.expired,
                 'why do you want to make an expired move?');
        _hash = sha256(abi.encodePacked(_nonce, _type));
    }



    // Funcion para recuperar una jugada con el nonce y el hash
    function getMoveFromHashAndNonce(bytes32 _hash, string memory _nonce
                                     ) public pure returns (MoveType _type) {
        if (_hash == makeMoveHash(_nonce, MoveType.rock)) {
            _type = MoveType.rock;
        } else if (_hash == makeMoveHash(_nonce, MoveType.paper)) {
            _type = MoveType.paper;
        } else if (_hash == makeMoveHash(_nonce, MoveType.scissors)) {
            _type = MoveType.scissors;
        } else {
            revert('Bad nonce');
        }
    }



    // Funcion para hacer una jugada con un hash de una jugada
    function makeAmove(bytes32 _hash) public payable returns (uint _index) {

        require(msg.value == bet, 'Bad value');

        _index = (moves.push(Move(now,          // timestamp
                                  _hash,        // hash de la jugada
                                  address(0),   // ahora no importa
                                  MoveType.rock // ahora no importa
                                  )) - 1); // devuelve el indice de la jugada

        // Emito el evento de una nueva jugada
        emit MakeAmove(msg.sender, _index);

    }



    // Funcion que muestra el indice de la jugada oponenete al
    // indice de una jugada dada
    function getOpponentIndex(uint _index
                              ) internal pure returns (uint _opponent_index) {
        if (_index%2 == 0) { // Indices pares
            _opponent_index = _index + 1 ;
        } else { // Indices inpares
            _opponent_index = _index - 1 ;
        }
    }



    // Funcion que devuleve el resutado entre dos posbiles jugadas
    function evalMove(MoveType _my_move, MoveType _op_move
                      ) internal pure returns (Result) {
        if (_op_move == MoveType.expired) {
            return Result.win;
        } else if (_my_move == MoveType.rock) {
            if (_op_move == MoveType.rock) {
                return Result.tie;
            } else if (_op_move == MoveType.scissors) {
                return Result.win;
            }
        } else if (_my_move == MoveType.paper) {
            if (_op_move == MoveType.rock) {
                return Result.win;
            } else if (_op_move == MoveType.paper) {
                return Result.tie;
            }
        } else if (_my_move == MoveType.scissors) {
            if (_op_move == MoveType.paper) {
                return Result.win;
            } else if (_op_move == MoveType.scissors) {
                return Result.tie;
            }
        }
        return Result.lose;
    }




    // Muestro una jugada pasando el indice
    function seeAmove(uint _index) public view returns (Result) {

        // Valido que se trate de un indice correto de jugada
        if (_index >= moves.length) {

            return Result.bad;

        } else {

            // Obtengo el indice de la jugada oponente
            uint opponent_index = getOpponentIndex(_index);

            if (opponent_index >= moves.length) {

                return Result.wait;

            } else if (moves[opponent_index].addr == address(0)) {

                return Result.opponent_not_showed;

            } else if (moves[_index].addr == address(0)) {

                return Result.not_showed;

            } else {

                // Obtengo la jugadas, evaluo y entrego la respuesta
                return evalMove(moves[_index]._type, moves[opponent_index]._type);

            }
        }
    }



    // Muestro mi jugada pasando el indice y el nonce con la que la arme
    // y de esta manera desmostrar cual fue mi jugada
    // Esto solo se debe poder hacer siemrpe y cuando ya tenga una jugada
    // oponenete
    function showMyMove(uint _index, string memory _nonce) public  {

        // Valido que se trate de un indice correto de jugada
        require(_index < moves.length, 'Bad index');

        // Valido que no haya sido mostrada antes...
        require(moves[_index].addr == address(0), 'Move already showed');

        // Obtengo el indice de la jugada oponente
        uint opponent_index = getOpponentIndex(_index);
        require(opponent_index < moves.length, 'Wait for an opponent');

        // Obtengo mi jugada con el hash guardado y el nonce que paso
        MoveType my_move = getMoveFromHashAndNonce(moves[_index].hash, _nonce);

        // Guardo los nuevos datos en la jugada
        moves[_index].addr      = msg.sender; // esto significa mostrado!
        moves[_index]._type     = my_move;
        moves[_index].timestamp = now;

        // Si mi oponente ya mostro su jugada veo quien gano...
        if (moves[opponent_index].addr != address(0)) {

            Result result = evalMove(my_move, moves[opponent_index]._type);

            // En funcion del resultado pago los premios
            if (result == Result.win) {

                // Si gano me transfiero el premio
                msg.sender.transfer(prize);

            } else if (result == Result.lose) {

                // Si pierdo el premio es para el oponente
                moves[opponent_index].addr.transfer(prize);

            } else if (result == Result.tie) {

                // Si hay enpate devuelvo las apuestas
                msg.sender.transfer(bet);
                moves[opponent_index].addr.transfer(bet);

            }

            // Si no hay empate me resguardo la comision
            if (result != Result.tie) {
                ownerCollect = ownerCollect + ((2 * bet) - prize);
            }

        }

    }



    // Funcion para reclamar el premmio de una jugada expirada
    function claimAnExpiredMove(uint _index) public  {

        // Valido que se trate de un indice correto de jugada
        require(_index < moves.length, 'Bad index');

        // Valido que se haya mostrado la jugada
        require(moves[_index].addr!=address(0), 'Move not yet showed');

        // Valido que la jugada oponente tambien haya sido expuesta
        uint opponent_index = getOpponentIndex(_index);
        require(moves[opponent_index].addr==address(0), 'Move already showed');

        // Verifico que la jugada este expirada FIX ME!!!
        require((now - moves[_index].timestamp) > moveTimeOut,
                'Not expired yet');

        // Guardo los nuevos datos en la jugada
        moves[opponent_index].addr = moves[_index].addr;
        moves[opponent_index]._type = MoveType.expired;

        // Pago el premio
        moves[_index].addr.transfer(prize);

        // Resguardo la comision
        ownerCollect = ownerCollect + ((2 * bet) - prize);

    }



    // Funcion para que el dueño pueda sacar su parte
    function collect() public onlyOwner  {
        owner.transfer(ownerCollect);
        ownerCollect = 0;
    }

}
