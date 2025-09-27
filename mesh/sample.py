from main_simulation import mesh_bridge

def my_processor(message_json):
    # Your business logic here
    return {"result": "processed"}

# Send message through mesh
input_msg = {
    "message_type": "alert",
    "network_type": "wifi",     # or "bluetooth"
    "data": {"location": "room1"}
}

response = mesh_bridge(input_msg, my_processor)
print(response["data"])  # Your processed result