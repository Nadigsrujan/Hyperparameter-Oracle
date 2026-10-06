#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "../../include/oracle.h"

// External Init Functions
void init_probabilistic();
void init_trees();
void init_graphs();
void init_core();

// External DS Functions
void bloom_add(double* params, int count);
bool bloom_check(double* params, int count);
void cms_add(double* params, int count);
void hll_add(double* params, int count);
void insert_trie(double* params, int count);
void add_history(double score);
void pq_push(int config_id, double priority);
int pq_pop();
void map_put(int key, double value);
void lru_access(int config_id);
void reservoir_add(int config_id);

// --- Global State ---
static Config config_store[1000];
static int config_count = 0;

// --- API Implementation ---

void oracle_init() {
    srand(time(NULL));
    init_probabilistic();
    init_trees();
    init_graphs();
    init_core();
    config_count = 0;
    printf("[Oracle] Initialized C Core with DSA Engine.\n");
}

void oracle_free() {
    // In a real app, we would free malloc'd memory (Trie, Graphs)
    printf("[Oracle] Shutting down.\n");
}

int register_config(double* params, int count) {
    if (bloom_check(params, count)) {
        // Duplicate detected by Bloom Filter
        return -1; 
    }

    if (config_count >= 1000) return -1; // Full

    int id = config_count++;
    config_store[id].id = id;
    config_store[id].param_count = count;
    for (int i = 0; i < count; i++) config_store[id].params[i] = params[i];
    config_store[id].score = 0.0;

    // Update Structures
    bloom_add(params, count);
    insert_trie(params, count);
    hll_add(params, count);
    reservoir_add(id);

    return id;
}

void update_score(int config_id, double score) {
    if (config_id < 0 || config_id >= config_count) return;

    config_store[config_id].score = score;
    
    // Update Structures
    map_put(config_id, score);
    cms_add(config_store[config_id].params, config_store[config_id].param_count);
    add_history(score);
    
    // If good score, add to LRU and Priority Queue for local search
    if (score > 0.7) { // Threshold
        lru_access(config_id);
        pq_push(config_id, score);
    }
}

void get_next_suggestion(double* out_params, int count) {
    // Strategy:
    // 1. 30% chance: Explore (Random)
    // 2. 70% chance: Exploit (Perturb best from PQ)
    
    int best_id = pq_pop();
    
    if (best_id != -1 && (rand() % 100) < 70) {
        // Exploit: Perturb the best found so far
        Config best = config_store[best_id];
        for (int i = 0; i < count; i++) {
            double noise = ((rand() % 200) - 100) / 1000.0; // +/- 0.1
            out_params[i] = best.params[i] + noise;
            if (out_params[i] < 0) out_params[i] = 0;
            if (out_params[i] > 1) out_params[i] = 1;
        }
        // Put it back in PQ for future use
        pq_push(best_id, best.score); 
    } else {
        // Explore: Random
        for (int i = 0; i < count; i++) {
            out_params[i] = (rand() % 1000) / 1000.0;
        }
    }
}
