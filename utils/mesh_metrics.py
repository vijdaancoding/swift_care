class MeshMetrics:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.total_initial_kb = 0.0
        self.total_vnode_output_kb = 0.0
        self.total_final_kb = 0.0
        self.call_count = 0
    
    def add_call(self, initial_kb, vnode_output_kb, final_kb):
        self.total_initial_kb += initial_kb
        self.total_vnode_output_kb += vnode_output_kb
        self.total_final_kb += final_kb
        self.call_count += 1
    
    def get_summary(self):
        return {
            'total_calls': self.call_count,
            'total_initial_kb': self.total_initial_kb,
            'total_vnode_output_kb': self.total_vnode_output_kb,
            'total_final_kb': self.total_final_kb,
            'total_bandwidth_kb': self.total_initial_kb + self.total_final_kb
        }

# Global instance
mesh_metrics = MeshMetrics()