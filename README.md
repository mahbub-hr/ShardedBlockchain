# ShardedBlockchain

submitting new tx:
curl -X POST -H "Content-Type: application/json" -d '{
 "sender": "d4ee26eee15148ee92c6cd394edd974e",
 "recipient": "someone-other-address",
 "amount": 5
}' "http://localhost:5000/transactions/new"

registering with anchor peer:
curl -X POST http://127.0.0.1:8001/register_with -H 'Content-Type: application/json' -d '{
"node_address": "http://127.0.0.1:8000"}'