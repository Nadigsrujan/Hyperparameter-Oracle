#ifndef ORACLE_H
#define ORACLE_H

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

// --- Definitions ---
#define MAX_PARAMS 10
#define BLOOM_SIZE 10000
#define CMS_WIDTH 1000
#define CMS_DEPTH 5
#define HLL_REGISTERS 1024

// --- Data Structures ---

// Hyperparameter Configuration
typedef struct {
    int id;
    double params[MAX_PARAMS]; // Normalized values [0, 1]
    int param_count;
    double score; // Accuracy or -Loss
} Config;

// --- API Functions ---

// Initialization & Cleanup
void oracle_init();
void oracle_free();

// Core Operations
int register_config(double* params, int count); // Returns Config ID, -1 if duplicate
void update_score(int config_id, double score);
void get_next_suggestion(double* out_params, int count);

// Probabilistic DS Accessors (for explainability)
bool bloom_check(double* params, int count);
int cms_estimate_frequency(int param_index, int bucket_index);
int hll_count_unique();

// Tree/Graph Accessors
double segment_tree_query_range(int start, int end);
double fenwick_query_prefix(int index);

#endif // ORACLE_H
