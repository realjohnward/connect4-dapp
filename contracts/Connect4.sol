pragma solidity >= 0.5.0 < 0.6.0;
pragma experimental ABIEncoderV2;


contract Connect4 {
    
    event LogConstructorInitiated(string nextStep);
    event announceWinner(string winStatement);

    uint[] rows;
    uint[] columns; 
    

    constructor() public {
        emit LogConstructorInitiated("Constructor was initiated");
        rows = [1,2,3,4,5,6];
        columns = [1,2,3,4,5,6,7];
        numGames = 0;
    }

    uint256 public numGames;
    Game[] games;
    
    
    struct Game {
        address winner;
        uint playersTurn;
        address[2] players;
        uint challengeDate;
        uint acceptChallengeMaxTime;
        bool challengeAccepted;
        uint maxStallTime;
        uint lastMoveTime;
        uint[2] antes;
        mapping(string => uint) state;
        mapping(address => uint) pendingReturns;
        bool isActive;
        bool isTie;
    }

    function challengeOpponent(address opponent, uint playersTurn, uint acceptChallengeMaxTime, uint maxStallTime) public payable returns (bool){
        require(playersTurn == 1 || playersTurn == 2, "playersTurn argument must be 1 or 2.");
        address[2] memory players = [msg.sender, opponent];
        uint[2] memory antes = [msg.value, 0];
        address winner;
        
        Game memory game = Game({winner: winner, playersTurn: playersTurn, players: players, 
                                acceptChallengeMaxTime: acceptChallengeMaxTime, challengeDate: now, lastMoveTime: now,
                                challengeAccepted: false, maxStallTime: maxStallTime, isActive: true, isTie: false, antes: antes});
        games.push(game);
        numGames++;
        return true;
    }
    
    function acceptChallenge(uint gameIndex) public payable returns (bool) {
        Game storage game = games[gameIndex];
        uint msgvalue = msg.value;
        require(game.challengeAccepted == false, "Challenge has already been accepted for this game.");
        require(msg.sender == game.players[1], "Invalid player for this game.");
        require(msg.value >= game.antes[0], "value must be greater or equal to game's required ante amount.");
        game.antes[1] = msg.value;
        game.challengeAccepted = true;
        game.lastMoveTime = now;
        return true;
    }
    
    function getGameAbstract(uint gameIndex) public view returns (string memory){
        Game storage game = games[gameIndex];
        string memory isActive;
        if(game.isActive == true){
            isActive = "1";
        } else {
            isActive = "0";
        }

        string memory challengeAccepted;
        if(game.challengeAccepted == true){
            challengeAccepted = "1";
        } else {
            challengeAccepted = "0";
        }

        string memory result;

        result = string(abi.encodePacked("Players:", addressToString(game.players[0]), ",", addressToString(game.players[1]), 
                        "|ChallengeDate:", uintToString(game.challengeDate), "|ChallengeAccepted:", challengeAccepted, "|GameActive:", isActive, 
                        "|Winner:", addressToString(game.winner), "|P1PendingReturns:", uintToString(game.pendingReturns[game.players[0]]), 
                        "|P2PendingReturns:", uintToString(game.pendingReturns[game.players[1]])));
        
        return result;
    }
    
    
    function getGameDetails(uint gameIndex) public view returns (string memory){
        Game storage game = games[gameIndex];

        string memory state;
        string memory s;
        for(uint i = 1; i < 8; i++){
            s = "";
            for(uint ii = 1; ii < 7; ii++){      
                s = string(abi.encodePacked(s, uintToString(i), ",", uintToString(ii), ":", uintToString(game.state[string(abi.encodePacked(uintToString(i), uintToString(ii)))]), ";"));
            }
            state = string(abi.encodePacked(state, s));
        }
        
        string memory isTie;
        if(game.isTie == true){
            isTie = "1";
        } else {
            isTie = "0";
        }
        
        state = string(abi.encodePacked("BoardState:", state, "|lastMoveTime:", uintToString(game.lastMoveTime), 
                            "|WhosTurn:", uintToString(game.playersTurn), "|TieGame:", isTie, "|MaxStallTime:", uintToString(game.maxStallTime), 
                            "|AcceptChallengeMaxTime:", uintToString(game.acceptChallengeMaxTime), "|P1Ante:", uintToString(game.antes[0]), 
                            "|P2Ante:", uintToString(game.antes[1])));
        
        return state;
    }


    function addressToString(address _addr) public pure returns(string memory) {
        bytes32 value = bytes32(uint256(_addr));
        bytes memory alphabet = "0123456789abcdef";

        bytes memory str = new bytes(42);
        str[0] = '0';
        str[1] = 'x';
        for (uint i = 0; i < 20; i++) {
            str[2+i*2] = alphabet[uint(uint8(value[i + 12] >> 4))];
            str[3+i*2] = alphabet[uint(uint8(value[i + 12] & 0x0f))];
        }
        return string(str);
    }
    
    function uintToString(uint _i) internal pure returns (string memory _uintAsString) {
        if (_i == 0) {
            return "0";
        }
        uint j = _i;
        uint len;
        while (j != 0) {
            len++;
            j /= 10;
        }
        bytes memory bstr = new bytes(len);
        uint k = len - 1;
        while (_i != 0) {
            bstr[k--] = byte(uint8(48 + _i % 10));
            _i /= 10;
        }
        return string(bstr);
    }

    function declareRefundDueToChallengeExpiration(uint gameIndex) public returns (bool) {
        Game storage game = games[gameIndex];
        require(game.challengeAccepted == false, "Cannot declare a refund when the game's challenge has already been accepted.");
        require(msg.sender == game.players[0], "Must be the challenger for this game to receive a refund.");
        require(now - game.challengeDate > game.acceptChallengeMaxTime, "The accept-challenge-max-time for this game has not been surpassed.");
        game.pendingReturns[msg.sender] += game.antes[0];
        game.isActive = false;
        return true;
    }
    
    function declareWinDueToOverstall(uint gameIndex) public returns (bool) {
        Game storage game = games[gameIndex];
        require(game.isActive == true, "Game is not active.");
        require(game.challengeAccepted == true, "Cannot declare a win when challenge hasn't been accepted.");
        require(now - game.lastMoveTime > game.maxStallTime, "This game's max stall time has not been surpassed.");
        if(msg.sender == game.players[0]){
            require(game.playersTurn == 2, "Cannot declare a opponent-overstall win when it's your turn.");
        } else if (msg.sender == game.players[1]) {
            require(game.playersTurn == 1, "Cannot declare a opponent-overstall win when it's your turn.");
        } else {
            return false;
        }
        
        game.pendingReturns[msg.sender] += (game.antes[0] + game.antes[1]);
        game.isActive = false;
        return true;
    }
    
    function isWinIsTie(uint gameIndex) internal view returns (bool, uint, bool) {
        Game storage game = games[gameIndex];
        
        bool isTie = true;
        string[4] memory combo;
        uint slotsTakenByP1;
        uint slotsTakenByP2;
        uint emptySlots;       
        
        // check vertical slopes for win/tie
        for(uint i = 1; i < 8; i++){
            for(uint ii = 0; ii < 3; ii++){
                slotsTakenByP1 = 0;
                slotsTakenByP2 = 0;
                emptySlots = 0;
                combo = [string(abi.encodePacked(uintToString(i), uintToString(1+ii))),
                        string(abi.encodePacked(uintToString(i), uintToString(2+ii))),
                        string(abi.encodePacked(uintToString(i), uintToString(3+ii))),
                        string(abi.encodePacked(uintToString(i), uintToString(4+ii)))];               
                for(uint iii = 0; iii < combo.length; iii++){
                    if(game.state[combo[iii]] == 1){
                        slotsTakenByP1 += 1;
                    } else if(game.state[combo[iii]] == 2){
                        slotsTakenByP2 += 1;
                    } else {
                        emptySlots += 1;
                    }
                }
                if(slotsTakenByP1 == 4){
                    return (true, 1, false);
                } else if(slotsTakenByP2 == 4){
                    return (true, 2, false);
                } else if((slotsTakenByP1 >= 1 && slotsTakenByP2 == 0) || (slotsTakenByP2 >= 1 && slotsTakenByP1 == 0)){
                    isTie = false;
                }         
            }            
        }

         // check horizontal slopes for win/tie
        for(uint i = 1; i < 7; i++){
            for(uint ii = 1; ii < 5; ii++){
                slotsTakenByP1 = 0;
                slotsTakenByP2 = 0;
                emptySlots = 0;
                combo = [string(abi.encodePacked(uintToString(ii), uintToString(i))),
                        string(abi.encodePacked(uintToString(1+ii), uintToString(i))),
                        string(abi.encodePacked(uintToString(2+ii), uintToString(i))),
                        string(abi.encodePacked(uintToString(3+ii), uintToString(i)))];
                for(uint iii = 0; iii < combo.length; iii++){
                    if(game.state[combo[iii]] == 1){
                        slotsTakenByP1 += 1;
                    } else if(game.state[combo[iii]] == 2){
                        slotsTakenByP2 += 1;
                    } else {
                        emptySlots += 1;
                    }
                }
                if(slotsTakenByP1 == 4){
                    return (true, 1, false);
                } else if(slotsTakenByP2 == 4){
                    return (true, 2, false);
                } else if((slotsTakenByP1 >= 1 && slotsTakenByP2 == 0) || (slotsTakenByP2 >= 1 && slotsTakenByP1 == 0)){
                    isTie = false;
                }
            }
        }
        
        uint8[2][4] memory possib4InRowStartCoords = [[1,3],[4,1],[1,4],[4,6]];

        // check positive slopes where each slope has 1 possible 4-in-row 
        for(uint i = 0; i < possib4InRowStartCoords.length; i++){
              slotsTakenByP1 = 0;
              slotsTakenByP2 = 0;
              emptySlots = 0;
              if(i <= 1){
              combo = [string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]), uintToString(possib4InRowStartCoords[i][1]))),
                    string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+1), uintToString(possib4InRowStartCoords[i][1]+1))),
                    string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+2), uintToString(possib4InRowStartCoords[i][1]+2))),
                    string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+3), uintToString(possib4InRowStartCoords[i][1]+3)))];
              } else {
              combo = [string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]), uintToString(possib4InRowStartCoords[i][1]))),
                    string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+1), uintToString(possib4InRowStartCoords[i][1]-1))),
                    string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+2), uintToString(possib4InRowStartCoords[i][1]-2))),
                    string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+3), uintToString(possib4InRowStartCoords[i][1]-3)))];
              }

              for(uint ii = 0; ii < combo.length; ii++){
                  if(game.state[combo[ii]] == 1){
                      slotsTakenByP1 += 1;
                  } else if(game.state[combo[ii]] == 2){
                      slotsTakenByP2 += 1;
                  } else {
                      emptySlots += 1;
                  }
              }
              if(slotsTakenByP1 == 4){
                  return (true, 1, false);
              } else if(slotsTakenByP2 == 4){
                  return (true, 2, false);
              } else if((slotsTakenByP1 >= 1 && slotsTakenByP2 == 0) || (slotsTakenByP2 >= 1 && slotsTakenByP1 == 0)){
                  isTie = false;
              }                          
            }
        
        
        possib4InRowStartCoords = [[1,2], [3,1], [1,5], [3,6]];
        
        // check positive slopes where each slope has 2 possible 4-in-row 
        for(uint i = 0; i < possib4InRowStartCoords.length; i++){
            for(uint ii = 0; ii < 2; ii++){
                slotsTakenByP1 = 0;
                slotsTakenByP2 = 0;
                emptySlots = 0;
                if(i <= 1){
                combo = [string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+ii), uintToString(possib4InRowStartCoords[i][1]+ii))),
                        string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+1+ii), uintToString(possib4InRowStartCoords[i][1]+1+ii))),
                        string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+2+ii), uintToString(possib4InRowStartCoords[i][1]+2+ii))),
                        string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+3+ii), uintToString(possib4InRowStartCoords[i][1]+3+ii)))];
                } else {
                combo = [string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+ii), uintToString(possib4InRowStartCoords[i][1]-ii))),
                        string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+1+ii), uintToString(possib4InRowStartCoords[i][1]-1-ii))),
                        string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+2+ii), uintToString(possib4InRowStartCoords[i][1]-2-ii))),
                        string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+3+ii), uintToString(possib4InRowStartCoords[i][1]-3-ii)))];
                }

                for(uint iii = 0; iii < combo.length; iii++){
                    if(game.state[combo[iii]] == 1){
                        slotsTakenByP1 += 1;
                    } else if(game.state[combo[iii]] == 2){
                        slotsTakenByP2 += 1;
                    } else {
                        emptySlots += 1;
                    }
                }
                if(slotsTakenByP1 == 4){
                    return (true, 1, false);
                } else if(slotsTakenByP2 == 4){
                    return (true, 2, false);
                } else if((slotsTakenByP1 >= 1 && slotsTakenByP2 == 0) || (slotsTakenByP2 >= 1 && slotsTakenByP1 == 0)){
                    isTie = false;
                }         
            }
        }        
        
        possib4InRowStartCoords = [[1,1], [2,1], [1,6], [2,6]];

         // check positive slopes where each slope has 3 possible 4-in-row 
        for(uint i = 0; i < possib4InRowStartCoords.length; i++){
            for(uint ii = 0; ii < 3; ii++){
                slotsTakenByP1 = 0;
                slotsTakenByP2 = 0;
                emptySlots = 0;
                if(i <= 1){
                combo = [string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+ii), uintToString(possib4InRowStartCoords[i][1]+ii))),
                        string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+1+ii), uintToString(possib4InRowStartCoords[i][1]+1+ii))),
                        string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+2+ii), uintToString(possib4InRowStartCoords[i][1]+2+ii))),
                        string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+3+ii), uintToString(possib4InRowStartCoords[i][1]+3+ii)))];
                } else {
                combo = [string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+ii), uintToString(possib4InRowStartCoords[i][1]-ii))),
                        string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+1+ii), uintToString(possib4InRowStartCoords[i][1]-1-ii))),
                        string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+2+ii), uintToString(possib4InRowStartCoords[i][1]-2-ii))),
                        string(abi.encodePacked(uintToString(possib4InRowStartCoords[i][0]+3+ii), uintToString(possib4InRowStartCoords[i][1]-3-ii)))];
                }

                for(uint iii = 0; iii < combo.length; iii++){
                    if(game.state[combo[iii]] == 1){
                        slotsTakenByP1 += 1;
                    } else if(game.state[combo[iii]] == 2){
                        slotsTakenByP2 += 1;
                    } else {
                        emptySlots += 1;
                    }
                }
                if(slotsTakenByP1 == 4){
                    return (true, 1, false);
                } else if(slotsTakenByP2 == 4){
                    return (true, 2, false);
                } else if((slotsTakenByP1 >= 1 && slotsTakenByP2 == 0) || (slotsTakenByP2 >= 1 && slotsTakenByP1 == 0)){
                    isTie = false;
                }         
            }
        }        
        
        return (false, 0, isTie);
    }
      
    function move(uint column, uint gameIndex, bool checkIfWonOrTie) public returns (bool) {
        Game storage game = games[gameIndex];
        require(game.isActive == true, "Game is not active.");
        require(game.challengeAccepted == true, "Challenge has not been accepted for this game.");
        require(game.players[game.playersTurn - 1] == msg.sender, "Either it's not your turn or you're an invalid player for this game.");

        bool columnsContainColumn;
        for(uint i = 0; i < columns.length; i++){
            if(column == columns[i]){
                columnsContainColumn = true;
                break;
            }
        }
    
        require(columnsContainColumn, "Column must be less than or equal to 7 and greater than 0");
        
        uint row = 7;
        for(uint i = 0; i < rows.length; i++){
            if(game.state[string(abi.encodePacked(uintToString(column), uintToString(rows[i])))] == 0){
                row = rows[i];
                break;
            }
        }
        require(row < 7, "No slot available for the specified column");
        
        string memory coordinate = string(abi.encodePacked(uintToString(column), uintToString(row)));
        
        game.state[coordinate] = game.playersTurn;
        
        bool result;
        
        if(checkIfWonOrTie == true){
            (bool won, uint winner, bool tie) = isWinIsTie(gameIndex);
            if(won == true){
                if(winner == 1){
                    game.winner = game.players[0];
                } else {
                    game.winner = game.players[1];
                }
                game.pendingReturns[game.winner] += (game.antes[0] + game.antes[1]);
                game.isActive = false;
                result = true;
            } else if(tie == true){
                game.isTie = true;
                game.pendingReturns[game.players[0]] += game.antes[0];
                game.pendingReturns[game.players[1]] += game.antes[1];
                result = true;
            } else {
                result = false;
            }
        } else {
            result = false;
        }

        if(game.playersTurn == 1){
            game.playersTurn = 2;
        } else {
            game.playersTurn = 1;
        }
        return result;

    }
    
    function withdraw(uint gameIndex) public returns (bool) {
        Game storage game = games[gameIndex];
        uint amount = game.pendingReturns[msg.sender];
        if (amount > 0) {
            // It is important to set this to zero because the recipient
            // can call this function again as part of the receiving call
            // before `send` returns.
            game.pendingReturns[msg.sender] = 0;

            if (!msg.sender.send(amount)) {
                // No need to call throw here, just reset the amount owing
                game.pendingReturns[msg.sender] = amount;
                return false;
            }
        }
        return true;
    }
    
}