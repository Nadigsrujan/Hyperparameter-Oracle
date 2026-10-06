#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../include/oracle.h"

// --- Globals for Tree Structures ---
#define MAX_HISTORY 1000
static double history_scores[MAX_HISTORY];
static double segment_tree[4 * MAX_HISTORY];
static double fenwick_tree[MAX_HISTORY + 1];
static int history_count = 0;

// --- Trie Structure (for Config Signatures) ---
typedef struct TrieNode {
    struct TrieNode* children[10]; // 10 buckets for discretized values
    bool is_end;
} TrieNode;

static TrieNode* root;

TrieNode* create_node() {
    TrieNode* node = (TrieNode*)malloc(sizeof(TrieNode));
    node->is_end = false;
    for (int i = 0; i < 10; i++) node->children[i] = NULL;
    return node;
}

void insert_trie(double* params, int count) {
    if (!root) root = create_node();
    TrieNode* curr = root;
    for (int i = 0; i < count; i++) {
        int idx = (int)(params[i] * 10); // Discretize to 0-9
        if (idx < 0) idx = 0;
        if (idx > 9) idx = 9;
        
        if (!curr->children[idx]) {
            curr->children[idx] = create_node();
        }
        curr = curr->children[idx];
    }
    curr->is_end = true;
}

// --- Segment Tree (Range Maximum Query) ---
void build_segment_tree(int node, int start, int end) {
    if (start == end) {
        segment_tree[node] = history_scores[start];
    } else {
        int mid = (start + end) / 2;
        build_segment_tree(2 * node, start, mid);
        build_segment_tree(2 * node + 1, mid + 1, end);
        segment_tree[node] = (segment_tree[2 * node] > segment_tree[2 * node + 1]) 
                             ? segment_tree[2 * node] 
                             : segment_tree[2 * node + 1];
    }
}

void update_segment_tree(int node, int start, int end, int idx, double val) {
    if (start == end) {
        segment_tree[node] = val;
    } else {
        int mid = (start + end) / 2;
        if (start <= idx && idx <= mid) {
            update_segment_tree(2 * node, start, mid, idx, val);
        } else {
            update_segment_tree(2 * node + 1, mid + 1, end, idx, val);
        }
        segment_tree[node] = (segment_tree[2 * node] > segment_tree[2 * node + 1]) 
                             ? segment_tree[2 * node] 
                             : segment_tree[2 * node + 1];
    }
}

double query_segment_tree(int node, int start, int end, int l, int r) {
    if (r < start || end < l) return -1e9; // Out of range
    if (l <= start && end <= r) return segment_tree[node];
    
    int mid = (start + end) / 2;
    double p1 = query_segment_tree(2 * node, start, mid, l, r);
    double p2 = query_segment_tree(2 * node + 1, mid + 1, end, l, r);
    return (p1 > p2) ? p1 : p2;
}

double segment_tree_query_range(int start, int end) {
    if (start < 0) start = 0;
    if (end >= history_count) end = history_count - 1;
    if (start > end) return 0.0;
    return query_segment_tree(1, 0, history_count - 1, start, end);
}

// --- Fenwick Tree (Prefix Sums for Rolling Average) ---
void update_fenwick(int idx, double val) {
    idx++; // 1-based index
    while (idx <= MAX_HISTORY) {
        fenwick_tree[idx] += val;
        idx += idx & (-idx);
    }
}

double query_fenwick(int idx) {
    idx++;
    double sum = 0;
    while (idx > 0) {
        sum += fenwick_tree[idx];
        idx -= idx & (-idx);
    }
    return sum;
}

double fenwick_query_prefix(int index) {
    if (index >= history_count) index = history_count - 1;
    return query_fenwick(index);
}

// --- Integration Helper ---
void add_history(double score) {
    if (history_count < MAX_HISTORY) {
        history_scores[history_count] = score;
        update_segment_tree(1, 0, MAX_HISTORY - 1, history_count, score);
        update_fenwick(history_count, score);
        history_count++;
    }
}

void init_trees() {
    memset(segment_tree, 0, sizeof(segment_tree));
    memset(fenwick_tree, 0, sizeof(fenwick_tree));
    root = NULL;
}
