from multiprocessing import Queue, Process
from mesh.agent_logic import VNode,CNode, run_relay_worker, run_c_worker


def mesh_bridge(input_json, processor_function, network_type="bluetooth"):
    """
    Args:
        input_json (dict): Input message 
        processor_function (callable): Function that processes the message
        network_type (str): "wifi" for direct route, "bluetooth" for relay route
    """
    print("\n" + "="*50)
    print("MESH BRIDGE - Message Processing Started")
    print("="*50)
    print(f"\n[MESH] Using {network_type.upper()} routing")
    
    if network_type.lower() == "wifi":
        print("Direct WiFi Route: V-Node → C-Node")
        
        v_node = VNode("V-NODE")
        c_node = CNode("C-NODE")
        
        processed_input = v_node.process_message(input_json.copy())
        processed_input["network_type"] = "wifi"
        
        response_json = c_node.process_message(processed_input, processor_function, use_direct_route=True)
        
    else:
        print("Bluetooth Route: V-Node → Relay → C-Node")
    
    
    # Create communication queues
    v_to_relay = Queue()
    relay_to_c = Queue()
    c_to_relay = Queue()
    relay_to_v = Queue()
    
    # Initialize V-Node
    v_node = VNode("V-NODE")
    
    # Start Relay and C-Node processes
    relay_process = Process(
        target=run_relay_worker,
        args=(v_to_relay, relay_to_c, c_to_relay, relay_to_v)
    )
    
    c_process = Process(
        target=run_c_worker,
        args=(relay_to_c, c_to_relay, processor_function)
    )
    
    relay_process.start()
    c_process.start()
    
    # V-Node processes input and sends to relay
    processed_input = v_node.process_message(input_json.copy())
    v_to_relay.put(processed_input)
    
    # Wait for response to come back through the mesh
    print("[V-Node] Waiting for response from mesh...")
    response_json = relay_to_v.get(timeout=10)
    
    # Clean up processes
    relay_process.join(timeout=2)
    c_process.join(timeout=2)
    
    if relay_process.is_alive():
        relay_process.terminate()
    if c_process.is_alive():
        c_process.terminate()
    
    print("[V-Node] Response received from mesh")
    print("="*50)
    print("MESH BRIDGE - Processing Complete")
    print("="*50)
    
    return response_json