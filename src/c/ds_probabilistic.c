#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "../../include/oracle.h"

// --- Globals for Probabilistic Structures ---
static uint8_t bloom_filter[BLOOM_SIZE / 8]; // Bit array
static int cms_table[CMS_DEPTH][CMS_WIDTH];
static uint8_t hll_registers[HLL_REGISTERS];

// --- Helper: MurmurHash3-like simple hash ---
uint32_t hash_params(double* params, int count, uint32_t seed) {
    uint32_t h = seed;
    for (int i = 0; i < count; i++) {
        // Discretize double to int for hashing (simple approach)
        int val = (int)(params[i] * 10000); 
        h ^= val;
        h *= 0x5bd1e995;
        h ^= h >> 15;
    }
    return h;
}

// --- Bloom Filter ---
void bloom_add(double* params, int count) {
    uint32_t h1 = hash_params(params, count, 0x1234);
    uint32_t h2 = hash_params(params, count, 0x5678);
    uint32_t h3 = hash_params(params, count, 0x9ABC);

    int idx1 = h1 % BLOOM_SIZE;
    int idx2 = h2 % BLOOM_SIZE;
    int idx3 = h3 % BLOOM_SIZE;

    bloom_filter[idx1 / 8] |= (1 << (idx1 % 8));
    bloom_filter[idx2 / 8] |= (1 << (idx2 % 8));
    bloom_filter[idx3 / 8] |= (1 << (idx3 % 8));
}

bool bloom_check(double* params, int count) {
    uint32_t h1 = hash_params(params, count, 0x1234);
    uint32_t h2 = hash_params(params, count, 0x5678);
    uint32_t h3 = hash_params(params, count, 0x9ABC);

    int idx1 = h1 % BLOOM_SIZE;
    int idx2 = h2 % BLOOM_SIZE;
    int idx3 = h3 % BLOOM_SIZE;

    bool b1 = bloom_filter[idx1 / 8] & (1 << (idx1 % 8));
    bool b2 = bloom_filter[idx2 / 8] & (1 << (idx2 % 8));
    bool b3 = bloom_filter[idx3 / 8] & (1 << (idx3 % 8));

    return b1 && b2 && b3;
}

// --- Count-Min Sketch ---
// Tracks frequency of "discretized" parameter values to find popular regions
void cms_add(double* params, int count) {
    for (int i = 0; i < count; i++) {
        int val = (int)(params[i] * 100); // Discretize to 100 bins
        for (int d = 0; d < CMS_DEPTH; d++) {
            uint32_t h = (val ^ (d * 0xF00D)) % CMS_WIDTH; 
            cms_table[d][h]++;
        }
    }
}

int cms_estimate_frequency(int param_index, int bucket_index) {
    // This is a simplified accessor for visualization
    // In reality, we'd query by param value
    if (bucket_index >= CMS_WIDTH || bucket_index < 0) return 0;
    
    // Return min count for a "dummy" query or specific depth
    // For simplicity, just returning the value at depth 0 for the bucket
    return cms_table[0][bucket_index];
}

// --- HyperLogLog ---
// Estimates cardinality of unique configs
void hll_add(double* params, int count) {
    uint32_t h = hash_params(params, count, 0xDEAD);
    int idx = h % HLL_REGISTERS;
    uint32_t w = h / HLL_REGISTERS;
    
    // Count leading zeros
    int rank = 1;
    while ((w & 1) == 0 && rank < 32) {
        w >>= 1;
        rank++;
    }
    
    if (rank > hll_registers[idx]) {
        hll_registers[idx] = rank;
    }
}

int hll_count_unique() {
    double alpha = 0.7213 / (1 + 1.079 / HLL_REGISTERS);
    double sum = 0.0;
    for (int i = 0; i < HLL_REGISTERS; i++) {
        sum += pow(2.0, -hll_registers[i]);
    }
    double estimate = alpha * HLL_REGISTERS * HLL_REGISTERS / sum;
    return (int)estimate;
}

// --- Init/Free for Probabilistic ---
void init_probabilistic() {
    memset(bloom_filter, 0, sizeof(bloom_filter));
    memset(cms_table, 0, sizeof(cms_table));
    memset(hll_registers, 0, sizeof(hll_registers));
}
