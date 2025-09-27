import uuid
import time


class VNode:
    def __init__(self, node_id):
        self.node_id = node_id
    
    def process_message(self, message_json):
        print(f"[V-Node] Received: {message_json}")
        
        # Add mesh metadata
        message_json["mesh_id"] = str(uuid.uuid4())[:8]
        message_json["timestamp"] = time.time()
        message_json["path"] = ["V-Node"]
        
        print(f"[V-Node] Processed and forwarding to Relay")
        return message_json


class RelayNode:
    def __init__(self, node_id):
        self.node_id = node_id
    
    def process_message(self, message_json):
        print(f"[Relay-Node] Received: {message_json}")
        
        # Update path
        message_json["path"].append("Relay-Node")
        
        print(f"[Relay-Node] Forwarding to C-Node")
        return message_json
    
    def process_response(self, response_json):
        print(f"[Relay-Node] Response received from C-Node")
        
        # Update path for response
        response_json["path"].append("Relay-Node-Return")
        
        print(f"[Relay-Node] Forwarding response to V-Node")
        return response_json


class CNode:
    def __init__(self, node_id):
        self.node_id = node_id
    
    def process_message(self, message_json, processor_function):
        print(f"[C-Node] Final destination reached: {message_json}")
        
        # Update path
        message_json["path"].append("C-Node")

        user_message = message_json.get("data", "")
        
        # Call the user's processor function
        print(f"[C-Node] Calling user processor function...")
        response_data = processor_function(user_message)

        if hasattr(response_data, "text"):
            response_text = response_data.text
        else:
            response_text = str(response_data)


        
        # Create response in same JSON structure
        response_json = {
            "message_type": "response",
            "network_type": message_json.get("network_type", "wifi"),
            "data": response_text,
            "original_mesh_id": message_json["mesh_id"],
            "response_id": str(uuid.uuid4())[:8],
            "timestamp": time.time(),
            "path": message_json["path"] + ["C-Node-Response"]
        }
        
        print(f"[C-Node] Generated response: {response_json}")
        return response_json


def run_relay_worker(input_queue, output_queue, response_input_queue, response_output_queue):
    relay = RelayNode("RELAY-1")
    
    # Handle forward message
    message = input_queue.get()
    processed_message = relay.process_message(message)
    output_queue.put(processed_message)
    
    # Handle response message
    response = response_input_queue.get()
    processed_response = relay.process_response(response)
    response_output_queue.put(processed_response)


def run_c_worker(input_queue, output_queue, processor_function):
    c_node = CNode("C-NODE")
    
    # Handle incoming message and generate response
    message = input_queue.get()
    response = c_node.process_message(message, processor_function)
    output_queue.put(response)