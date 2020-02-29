module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "*", // Match any network id
      //from: "bb2ab5cdf7123ba6a479a6967aa68186f156ee62",
      from: "0xd796b936cc780059a752255a8161222358687c24"
    },
    rinkeby: {
      host: "localhost",
      port: 8545,
      network_id: 4,
      gas: 9000000
    }
  },
  solc: {
    optimizer: {
      enabled: true,
      runs: 200
    }
  }
}
