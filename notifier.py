from coinbase.wallet.client import Client

# Do not give valid auth data, as we won't use anything that requires an account
client = Client("void", "void")
print(client.get_spot_price(currency_pair="BTC-USD"))
