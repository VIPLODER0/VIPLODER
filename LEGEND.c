
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include <unistd.h>

#define MAX_THREADS 100
#define BUFFER_SIZE 2048

typedef struct {
    char target[256];
    int port;
    int duration;
    int thread_id;
} attack_params;

void log_activity(const char* message) {
    FILE* log_file = fopen("attack_log.txt", "a");
    if (log_file) {
        fprintf(log_file, "%s
", message);
        fclose(log_file);
    }
}

void* perform_attack(void* args) {
    attack_params* params = (attack_params*)args;
    char buffer[BUFFER_SIZE];
    memset(buffer, 'X', sizeof(buffer));

    char log_message[512];
    snprintf(log_message, sizeof(log_message), 
             "Thread %d: Initiating attack on %s:%d for %d seconds.", 
             params->thread_id, params->target, params->port, params->duration);
    log_activity(log_message);

    printf("Thread %d: Attacking %s:%d for %d seconds...
", 
            params->thread_id, params->target, params->port, params->duration);

    time_t end_time = time(NULL) + params->duration;
    int packets_sent = 0;

    while (time(NULL) < end_time) {
        // Simulate sending packets
        packets_sent++;
        snprintf(log_message, sizeof(log_message), 
                 "Thread %d: Sent packet #%d to %s:%d", 
                 params->thread_id, packets_sent, params->target, params->port);
        log_activity(log_message);
        usleep(100000); // Delay to simulate network traffic
    }

    snprintf(log_message, sizeof(log_message), 
             "Thread %d: Attack completed. Total packets sent: %d", 
             params->thread_id, packets_sent);
    log_activity(log_message);

    printf("Thread %d: Attack finished. Packets sent: %d
", params->thread_id, packets_sent);
    return NULL;
}

int validate_inputs(const char* target_ip, int port, int duration) {
    if (strlen(target_ip) < 7 || strlen(target_ip) > 15) {
        fprintf(stderr, "Error: Invalid IP address format.
");
        return 0;
    }
    if (port < 1 || port > 65535) {
        fprintf(stderr, "Error: Port must be between 1 and 65535.
");
        return 0;
    }
    if (duration <= 0) {
        fprintf(stderr, "Error: Duration must be greater than 0.
");
        return 0;
    }
    return 1;
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <target_ip> <port> <duration>
", argv[0]);
        return 1;
    }

    char* target_ip = argv[1];
    int port = atoi(argv[2]);
    int duration = atoi(argv[3]);

    if (!validate_inputs(target_ip, port, duration)) {
        return 1;
    }

    pthread_t threads[MAX_THREADS];
    attack_params params[MAX_THREADS];

    for (int i = 0; i < MAX_THREADS; i++) {
        snprintf(params[i].target, sizeof(params[i].target), "%s", target_ip);
        params[i].port = port;
        params[i].duration = duration;
        params[i].thread_id = i;

        if (pthread_create(&threads[i], NULL, perform_attack, &params[i]) != 0) {
            fprintf(stderr, "Error creating thread %d
", i);
            return 1;
        }
    }

    for (int i = 0; i < MAX_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("All attacks completed successfully.
");
    return 0;
}
