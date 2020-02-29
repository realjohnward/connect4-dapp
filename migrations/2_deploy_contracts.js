var Connect4 = artifacts.require("./Connect4.sol");

module.exports = function(deployer) {
  deployer.deploy(Connect4);
};