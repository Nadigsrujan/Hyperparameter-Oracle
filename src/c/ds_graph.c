#include <stdio.h>
#include <stdlib.h>
#include "../../include/oracle.h"

// --- Union-Find (Disjoint Set Union) ---
#define MAX_CONFIGS 1000
static int parent[MAX_CONFIGS];
static int rank[MAX_CONFIGS];

void make_set(int v) {
    parent[v] = v;
    rank[v] = 0;
}

int find_set(int v) {
    if (v == parent[v]) return v;
    return parent[v] = find_set(parent[v]);
}

void union_sets(int a, int b) {
    a = find_set(a);
    b = find_set(b);
    if (a != b) {
        if (rank[a] < rank[b]) {
            int temp = a; a = b; b = temp;
        }
        parent[b] = a;
        if (rank[a] == rank[b]) rank[a]++;
    }
}

// --- DAG (Directed Acyclic Graph) ---
// Adjacency list to track improvements: A -> B means B is an improvement over A
typedef struct Edge {
    int to;
    struct Edge* next;
} Edge;

static Edge* adj[MAX_CONFIGS];

void add_edge(int u, int v) {
    Edge* edge = (Edge*)malloc(sizeof(Edge));
    edge->to = v;
    edge->next = adj[u];
    adj[u] = edge;
}

// --- Init ---
void init_graphs() {
    for (int i = 0; i < MAX_CONFIGS; i++) {
        make_set(i);
        adj[i] = NULL;
    }
}
