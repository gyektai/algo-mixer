# algo-mixer
Mixer for the algorand blockchain.

How to use:

Deploy the smart contract. It is reusable.

Group the transactions in an array where the payments to the smart contract all come before the smart contract call. Have someone send the application call, and in it have the args of the contract call be the amounts and the accounts array being the accounts the amounts are going to, respectively.

The order is very important here, as in the first account of the accounts array will get the amount that comes first in the args array.

Accounts can send to multiple accounts, and transactions can be for varying amounts. For the best anonymity after sending, the output amounts should be similar, and as many addresses should take part.
