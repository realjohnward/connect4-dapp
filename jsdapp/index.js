console.log("index.js");
// var Web3 = require('web3');
var web3 = new Web3('https://rinkeby.infura.io/v3/4a5ea769a92c447597af8491f69ca939')

var abi = [
    {
      "inputs": [],
      "payable": false,
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": false,
          "name": "nextStep",
          "type": "string"
        }
      ],
      "name": "LogConstructorInitiated",
      "type": "event"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": false,
          "name": "winStatement",
          "type": "string"
        }
      ],
      "name": "announceWinner",
      "type": "event"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "opponent",
          "type": "address"
        },
        {
          "name": "playersTurn",
          "type": "uint256"
        },
        {
          "name": "anteAmount",
          "type": "uint256"
        },
        {
          "name": "acceptChallengeMaxTime",
          "type": "uint256"
        },
        {
          "name": "maxStallTime",
          "type": "uint256"
        }
      ],
      "name": "challengeOpponent",
      "outputs": [
        {
          "name": "",
          "type": "bool"
        }
      ],
      "payable": true,
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "gameIndex",
          "type": "uint256"
        }
      ],
      "name": "acceptChallenge",
      "outputs": [
        {
          "name": "",
          "type": "bool"
        }
      ],
      "payable": true,
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "gameIndex",
          "type": "uint256"
        }
      ],
      "name": "getGameAbstract",
      "outputs": [
        {
          "name": "",
          "type": "string"
        }
      ],
      "payable": false,
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "gameIndex",
          "type": "uint256"
        }
      ],
      "name": "getGameDetails",
      "outputs": [
        {
          "name": "",
          "type": "string"
        }
      ],
      "payable": false,
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "gameIndex",
          "type": "uint256"
        }
      ],
      "name": "declareRefund",
      "outputs": [
        {
          "name": "",
          "type": "bool"
        }
      ],
      "payable": false,
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "gameIndex",
          "type": "uint256"
        }
      ],
      "name": "declareWinDueToOverstall",
      "outputs": [
        {
          "name": "",
          "type": "bool"
        }
      ],
      "payable": false,
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "gameIndex",
          "type": "uint256"
        }
      ],
      "name": "requestTieGame",
      "outputs": [
        {
          "name": "",
          "type": "bool"
        }
      ],
      "payable": false,
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "gameIndex",
          "type": "uint256"
        }
      ],
      "name": "rejectTieGameRequest",
      "outputs": [
        {
          "name": "",
          "type": "bool"
        }
      ],
      "payable": false,
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "row",
          "type": "uint256"
        },
        {
          "name": "column",
          "type": "uint256"
        },
        {
          "name": "gameIndex",
          "type": "uint256"
        }
      ],
      "name": "move",
      "outputs": [
        {
          "name": "",
          "type": "bool"
        }
      ],
      "payable": false,
      "stateMutability": "nonpayable",
      "type": "function"
    }
  ]

var contractAddress = '0xFb656C66be5a948c21c6C56D2D62F93a8C2D62D1'

var contract = new web3.eth.Contract(abi, contractAddress)


function challengeOpponent(){
    var from = $("#from").val();
    var opponent = $("#opponent").val();
    var playersTurn = $("#playersTurn").val();
    var anteAmount = $("#anteAmount").val();
    var acceptChallengeMaxTime = $("#acceptChallengeMaxTime").val();
    var maxStallTime = $("#maxStallTime").val();
    var gas = $("#gas").val();   
    var password = $("#password").val();
    var privkeyjson = $("#privkeyjson").val();
    var privateKey = keythereum.recover(password, JSON.parse(privkeyjson));
    console.log("privkey: %s", privateKey.toString('hex'));
    var data = contract.methods.challengeOpponent(opponent, parseInt(playersTurn), parseInt(anteAmount), 
                                                parseInt(acceptChallengeMaxTime), parseInt(maxStallTime)).encodeABI();
    
    
    web3.eth.getTransactionCount(from, (err, txCount) => {
    var txParams = {
            nonce: web3.utils.toHex(txCount),
            gasLimit: web3.utils.toHex(parseInt(gas)),
            gasPrice: web3.utils.toHex(web3.utils.toWei('10', 'gwei')),
            to: contractAddress,
            value: parseInt(anteAmount),
            data: data
        }       
        var tx = new ethereumjs.Tx(txParams);
        tx.sign(privateKey);
        const serializedTx = tx.serialize();
        const raw = '0x' + serializedTx.toString('hex');

        web3.eth.sendSignedTransaction(raw, (err, txHash) => {
            console.log('err:', err, 'txHash:', txHash)
        })
    })

}

function acceptChallenge(from, gameIndex, anteAmount, gas){
    contract.acceptChallenge(gameIndex, {from: from, value: anteAmount, gas: gas});
}

function getGameAbstract(gameIndex){
    contract.methods.getGameAbstract(gameIndex).call((err, result) => { console.log(result)})
}

function getGameDetails(gameIndex){
    contract.methods.getGameAbstract(gameIndex).call((err, result) => { console.log(result)})
}