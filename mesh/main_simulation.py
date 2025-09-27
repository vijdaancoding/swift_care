import threading
import queue
from mesh.agent_logic import VNode, run_relay_worker, run_c_worker
from utils.global_history import add_user, add_model
from utils.sizeof import get_size_kb


def mesh_bridge(input_json, processor_function, agent_name: str = "unknown"):
    """
    Args:
        input_json (dict): Input message 
        processor_function (callable): Function that processes the message
        network_type (str): "wifi" for direct route, "bluetooth" for relay route
    """
    print("\n" + "="*50)
    print("MESH BRIDGE - Message Processing Started")
    print("="*50)

    user_message = input_json.get("data", "")
    add_user(user_message, agent_name)
    
    network_type = input_json.get("network_type", "bluetooth")

    # Initialize V-Node
    v_node = VNode("V-NODE")
    response_json = {}
     
    # -- Size Tracking --
    initial_size_kb = get_size_kb(input_json)
    print(f"[Metrics] Initial request size: {initial_size_kb:.4f} KB")


    # ----------
    # WiFi Direct
    # ----------
    if network_type == "wifi":
        print("[System] Executing DIRECT WiFi route (V-Node -> C-Node)")
        v_to_c = queue.Queue()
        c_to_v = queue.Queue()

        c_thread = threading.Thread(
            target=run_c_worker,
            args=(v_to_c, c_to_v, processor_function, True) # Pass True for direct route
        )
        c_thread.start()

        # V-Node sends directly to C-Node
        processed_input = v_node.process_message(input_json.copy())
        v_to_c.put(processed_input)
        
        # Wait for direct response from C-Node
        print("[V-Node] Waiting for DIRECT response from C-Node...")
        response_json = c_to_v.get(timeout=30)
        c_thread.join(timeout=2)

    # ------------
    # BLUETOOTH
    # ------------

    else:
        print("[System] Executing RELAY MESH (Bluetooth) route")

    
        # Create communication queues
        v_to_relay = queue.Queue()
        relay_to_c = queue.Queue()
        c_to_relay = queue.Queue()
        relay_to_v = queue.Queue()
    
    
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
        v_node_output_size_kb = get_size_kb(processed_input)
        print(f"[Metrics] V-Node output size: {v_node_output_size_kb:.4f} KB")
        v_to_relay.put(processed_input)
        
        # Wait for response to come back through the mesh
        print("[V-Node] Waiting for response from mesh...")
        response_json = relay_to_v.get(timeout=30)

        assistant_message = response_json.get("data", "")
        add_model(assistant_message, agent_name)
        
        # Clean up processes
        relay_thread.join(timeout=2)
        c_thread.join(timeout=2)
    
    
    final_size_kb = get_size_kb(response_json)
    print(f"[Metrics] Final response size: {final_size_kb:.4f} KB")
    
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