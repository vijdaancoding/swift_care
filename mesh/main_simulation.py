import threading
import queue
from mesh.agent_logic import VNode, run_relay_worker, run_c_worker
from utils.global_history import add_user, add_model


def mesh_bridge(input_json, processor_function, agent_name: str = "unknown"):
    """
    Simple mesh bridge function that takes JSON input and returns JSON response.
    
    Args:
        input_json (dict): Input message with fields like message_type, network_type, data
        processor_function (callable): Function that processes the message at C-Node
    
    Returns:
        dict: Response JSON with same structure
    """
    print("\n" + "="*50)
    print("MESH BRIDGE - Message Processing Started")
    print("="*50)

    user_message = input_json.get("data", "")
    add_user(user_message, agent_name)
    
    # Create communication queues
    v_to_relay = queue.Queue()
    relay_to_c = queue.Queue()
    c_to_relay = queue.Queue()
    relay_to_v = queue.Queue()
    
    # Initialize V-Node
    v_node = VNode("V-NODE")
    
    # Start Relay and C-Node processes
    relay_thread = threading.Thread(
        target=run_relay_worker,
        args=(v_to_relay, relay_to_c, c_to_relay, relay_to_v)
    )
    
    c_thread = threading.Thread(
        target=run_c_worker,
        args=(relay_to_c, c_to_relay, processor_function)
    )
    
    relay_thread.start()
    c_thread.start()
    
    # V-Node processes input and sends to relay
    processed_input = v_node.process_message(input_json.copy())
    v_to_relay.put(processed_input)
    
    # Wait for response to come back through the mesh
    print("[V-Node] Waiting for response from mesh...")
    response_json = relay_to_v.get(timeout=30)

    assistant_message = response_json.get("data", "")
    add_model(assistant_message, agent_name)
    
    # Clean up processes
    relay_thread.join(timeout=2)
    c_thread.join(timeout=2)
    
    
    print("[V-Node] Response received from mesh")
    print("="*50)
    print("MESH BRIDGE - Processing Complete")
    print("="*50)
    
    return response_json


def mesh_bridge_legacy(input_json, processor_function):
    """
    Legacy mesh bridge without history (for backward compatibility)
    """
    return mesh_bridge(input_json, processor_function, "legacy")