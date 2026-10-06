#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../include/oracle.h"

// --- Priority Queue (Max Heap) ---
// Stores Config IDs ordered by potential/score
typedef struct {
    int config_id;
    double priority;
} HeapNode;

#define MAX_HEAP_SIZE 1000
static HeapNode heap[MAX_HEAP_SIZE];
static int heap_size = 0;

void swap_heap(int i, int j) {
    HeapNode temp = heap[i];
    heap[i] = heap[j];
    heap[j] = temp;
}

void pq_push(int config_id, double priority) {
    if (heap_size >= MAX_HEAP_SIZE) return; // Full
    int i = heap_size++;
    heap[i].config_id = config_id;
    heap[i].priority = priority;
    
    // Bubble up
    while (i > 0) {
        int p = (i - 1) / 2;
        if (heap[p].priority >= heap[i].priority) break;
        swap_heap(i, p);
        i = p;
    }
}

int pq_pop() {
    if (heap_size == 0) return -1;
    int ret = heap[0].config_id;
    heap[0] = heap[--heap_size];
    
    // Bubble down
    int i = 0;
    while (2 * i + 1 < heap_size) {
        int left = 2 * i + 1;
        int right = 2 * i + 2;
        int largest = i;
        
        if (left < heap_size && heap[left].priority > heap[largest].priority) largest = left;
        if (right < heap_size && heap[right].priority > heap[largest].priority) largest = right;
        
        if (largest == i) break;
        swap_heap(i, largest);
        i = largest;
    }
    return ret;
}

// --- Hash Map (Simple Linear Probing) ---
// Maps Config ID -> Score
#define HASH_MAP_SIZE 2048
typedef struct {
    int key; // Config ID
    double value; // Score
    bool occupied;
} HashEntry;

static HashEntry hash_map[HASH_MAP_SIZE];

void map_put(int key, double value) {
    int idx = key % HASH_MAP_SIZE;
    while (hash_map[idx].occupied && hash_map[idx].key != key) {
        idx = (idx + 1) % HASH_MAP_SIZE;
    }
    hash_map[idx].key = key;
    hash_map[idx].value = value;
    hash_map[idx].occupied = true;
}

double map_get(int key) {
    int idx = key % HASH_MAP_SIZE;
    while (hash_map[idx].occupied) {
        if (hash_map[idx].key == key) return hash_map[idx].value;
        idx = (idx + 1) % HASH_MAP_SIZE;
    }
    return -1.0; // Not found
}

// --- LRU Cache ---
// Stores recently successful Config IDs
#define LRU_CAPACITY 10
int lru_cache[LRU_CAPACITY];
int lru_count = 0;

void lru_access(int config_id) {
    // Check if exists
    int idx = -1;
    for (int i = 0; i < lru_count; i++) {
        if (lru_cache[i] == config_id) {
            idx = i;
            break;
        }
    }
    
    // Move to front
    if (idx != -1) {
        for (int i = idx; i > 0; i--) lru_cache[i] = lru_cache[i-1];
    } else {
        if (lru_count < LRU_CAPACITY) lru_count++;
        for (int i = lru_count - 1; i > 0; i--) lru_cache[i] = lru_cache[i-1];
    }
    lru_cache[0] = config_id;
}

// --- Reservoir Sampling ---
// Keeps a representative sample of all configs seen
#define RESERVOIR_SIZE 20
static int reservoir[RESERVOIR_SIZE];
static int total_seen = 0;

void reservoir_add(int config_id) {
    if (total_seen < RESERVOIR_SIZE) {
        reservoir[total_seen] = config_id;
    } else {
        int j = rand() % (total_seen + 1);
        if (j < RESERVOIR_SIZE) {
            reservoir[j] = config_id;
        }
    }
    total_seen++;
}

// --- Init ---
void init_core() {
    heap_size = 0;
    memset(hash_map, 0, sizeof(hash_map));
    lru_count = 0;
    total_seen = 0;
}
