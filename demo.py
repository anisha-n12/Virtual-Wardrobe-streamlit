from gradio_client import Client

# ⚠️ Use the exact Space ID you are targeting
client = Client("mr-dee/virtual-try-on") 

# This command prints all available API endpoints
client.view_api()