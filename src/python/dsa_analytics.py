"""
DSA Analytics Dashboard
Tracks and reports on all data structure activities during optimization
"""

class DSAAnalytics:
    def __init__(self):
        self.metrics = {
            'hash_map': {
                'name': 'Hash Map',
                'role': 'Stores performance of each config',
                'total_configs': 0,
                'unique_configs': 0,
                'collisions': 0,
                'lookups': 0
            },
            'segment_tree': {
                'name': 'Segment Tree',
                'role': 'Tracks best/worst scores over trial ranges',
                'best_score': 0.0,
                'worst_score': 1.0,
                'range_queries': 0,
                'updates': 0
            },
            'fenwick_tree': {
                'name': 'Fenwick Tree',
                'role': 'Calculates rolling averages and trends',
                'moving_average': 0.0,
                'trend': 'neutral',
                'updates': 0,
                'queries': 0
            },
            'dag': {
                'name': 'Directed Acyclic Graph',
                'role': 'Tracks improvement paths between configs',
                'nodes': 0,
                'edges': 0,
                'improvement_paths': 0,
                'dead_ends': 0
            },
            'union_find': {
                'name': 'Union-Find (Disjoint Set)',
                'role': 'Clusters similar performing configs',
                'clusters': 0,
                'successful_cluster': None,
                'failed_cluster': None,
                'unions': 0
            },
            'count_min_sketch': {
                'name': 'Count-Min Sketch',
                'role': 'Tracks frequently successful parameter values',
                'top_c_range': None,
                'top_gamma_range': None,
                'top_kernel': None,
                'queries': 0
            },
            'lru_cache': {
                'name': 'LRU Cache',
                'role': 'Remembers top-performing configurations',
                'cache_size': 10,
                'cache_hits': 0,
                'cache_misses': 0,
                'evictions': 0,
                'cached_configs': []
            },
            'reservoir_sampling': {
                'name': 'Reservoir Sampling',
                'role': 'Maintains representative sample of all runs',
                'reservoir_size': 50,
                'total_sampled': 0,
                'sample_diversity': 0.0,
                'representative_configs': []
            },
            'priority_queue': {
                'name': 'Priority Queue',
                'role': 'Selects best next configs to explore',
                'queue_size': 0,
                'insertions': 0,
                'extractions': 0,
                'top_priority': None
            }
        }
        
        # Historical data for trends
        self.score_history = []
        self.lru_cache_data = []
        self.reservoir_sample = []
        
    def update_hash_map(self, config_id, is_unique, had_collision=False):
        """Update hash map metrics"""
        self.metrics['hash_map']['total_configs'] += 1
        if is_unique:
            self.metrics['hash_map']['unique_configs'] += 1
        if had_collision:
            self.metrics['hash_map']['collisions'] += 1
        self.metrics['hash_map']['lookups'] += 1
    
    def update_segment_tree(self, score, iteration):
        """Update segment tree with new score"""
        self.metrics['segment_tree']['updates'] += 1
        if score > self.metrics['segment_tree']['best_score']:
            self.metrics['segment_tree']['best_score'] = score
        if score < self.metrics['segment_tree']['worst_score']:
            self.metrics['segment_tree']['worst_score'] = score
        self.metrics['segment_tree']['range_queries'] += 1
    
    def update_fenwick_tree(self, score):
        """Update Fenwick tree for moving averages"""
        self.score_history.append(score)
        self.metrics['fenwick_tree']['updates'] += 1
        
        # Calculate moving average (last 10 scores)
        if len(self.score_history) >= 10:
            recent = self.score_history[-10:]
            self.metrics['fenwick_tree']['moving_average'] = sum(recent) / len(recent)
            
            # Determine trend
            if len(self.score_history) >= 20:
                older_avg = sum(self.score_history[-20:-10]) / 10
                newer_avg = self.metrics['fenwick_tree']['moving_average']
                
                if newer_avg > older_avg + 0.01:
                    self.metrics['fenwick_tree']['trend'] = '📈 improving'
                elif newer_avg < older_avg - 0.01:
                    self.metrics['fenwick_tree']['trend'] = '📉 declining'
                else:
                    self.metrics['fenwick_tree']['trend'] = '➡️ stable'
        
        self.metrics['fenwick_tree']['queries'] += 1
    
    def update_dag(self, improved=False):
        """Update DAG metrics"""
        self.metrics['dag']['nodes'] += 1
        if improved:
            self.metrics['dag']['edges'] += 1
            self.metrics['dag']['improvement_paths'] += 1
        else:
            self.metrics['dag']['dead_ends'] += 1
    
    def update_union_find(self, score, cluster_id):
        """Update Union-Find clustering"""
        self.metrics['union_find']['unions'] += 1
        
        # Track successful vs failed clusters
        if score > 0.8:
            self.metrics['union_find']['successful_cluster'] = cluster_id
        elif score < 0.5:
            self.metrics['union_find']['failed_cluster'] = cluster_id
        
        # Estimate number of clusters (simplified)
        self.metrics['union_find']['clusters'] = max(
            self.metrics['union_find']['clusters'],
            cluster_id + 1
        )
    
    def update_count_min_sketch(self, params):
        """Update Count-Min Sketch for frequent parameters"""
        self.metrics['count_min_sketch']['queries'] += 1
        
        # Track most common ranges
        c_val = params.get('C', 0)
        gamma_val = params.get('gamma', 0)
        kernel = params.get('kernel', 'unknown')
        
        # Simplified: store top values (in real implementation, use actual CMS)
        if c_val > 0:
            if isinstance(c_val, (int, float)):
                self.metrics['count_min_sketch']['top_c_range'] = f"{c_val:.2f}"
        
        if isinstance(gamma_val, (int, float)):
            self.metrics['count_min_sketch']['top_gamma_range'] = f"{gamma_val:.4f}"
        
        self.metrics['count_min_sketch']['top_kernel'] = kernel
    
    def update_lru_cache(self, config, score, is_hit=False):
        """Update LRU cache"""
        if is_hit:
            self.metrics['lru_cache']['cache_hits'] += 1
        else:
            self.metrics['lru_cache']['cache_misses'] += 1
        
        # Add to cache (simplified LRU logic)
        cache_entry = {'config': config, 'score': score}
        
        # Remove if already exists
        self.lru_cache_data = [c for c in self.lru_cache_data if c['config'] != config]
        
        # Add to front
        self.lru_cache_data.insert(0, cache_entry)
        
        # Limit size
        if len(self.lru_cache_data) > self.metrics['lru_cache']['cache_size']:
            self.lru_cache_data.pop()
            self.metrics['lru_cache']['evictions'] += 1
        
        # Store top configs
        sorted_cache = sorted(self.lru_cache_data, key=lambda x: x['score'], reverse=True)
        self.metrics['lru_cache']['cached_configs'] = [
            {'params': c['config'], 'score': c['score']} 
            for c in sorted_cache[:5]
        ]
    
    def update_reservoir_sampling(self, config, score):
        """Update reservoir sample"""
        self.metrics['reservoir_sampling']['total_sampled'] += 1
        
        # Reservoir sampling algorithm
        k = self.metrics['reservoir_sampling']['reservoir_size']
        n = self.metrics['reservoir_sampling']['total_sampled']
        
        if len(self.reservoir_sample) < k:
            self.reservoir_sample.append({'config': config, 'score': score})
        else:
            # Replace with probability k/n
            import random
            j = random.randint(0, n - 1)
            if j < k:
                self.reservoir_sample[j] = {'config': config, 'score': score}
        
        # Calculate diversity (simplified: unique kernel types)
        if self.reservoir_sample:
            kernels = set(c['config'].get('kernel', 'unknown') for c in self.reservoir_sample)
            self.metrics['reservoir_sampling']['sample_diversity'] = len(kernels) / 4.0  # 4 kernel types
        
        # Store representative sample
        self.metrics['reservoir_sampling']['representative_configs'] = [
            {'params': c['config'], 'score': c['score']} 
            for c in self.reservoir_sample[:5]
        ]
    
    def update_priority_queue(self, queue_size, top_score=None):
        """Update priority queue metrics"""
        self.metrics['priority_queue']['queue_size'] = queue_size
        self.metrics['priority_queue']['insertions'] += 1
        if top_score is not None:
            self.metrics['priority_queue']['top_priority'] = top_score
    
    def extract_from_priority_queue(self):
        """Record extraction from priority queue"""
        self.metrics['priority_queue']['extractions'] += 1
    
    def get_all_metrics(self):
        """Get all DSA metrics"""
        return self.metrics
    
    def get_summary(self):
        """Get a human-readable summary"""
        summary = []
        
        summary.append("=== DSA ANALYTICS DASHBOARD ===\n")
        
        for key, ds in self.metrics.items():
            summary.append(f"\n{ds['name']}:")
            summary.append(f"  Role: {ds['role']}")
            
            # Add specific metrics for each DS
            for metric_key, metric_value in ds.items():
                if metric_key not in ['name', 'role'] and metric_value is not None:
                    summary.append(f"  {metric_key}: {metric_value}")
        
        return "\n".join(summary)
