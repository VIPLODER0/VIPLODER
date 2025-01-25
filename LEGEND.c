
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
const unsigned char MY_AES_KEY[16] = "MySuperSafeKey12";
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

// Function for AES encryption demonstration
void aes_encrypt_demo(const unsigned char *plaintext, unsigned char *ciphertext) {
    AES_KEY encryptKey;
    AES_set_encrypt_key(MY_AES_KEY, 128, &encryptKey);
    AES_cbc_encrypt(plaintext, ciphertext, strlen((const char *)plaintext), &encryptKey, (unsigned char *)AES_IV, AES_ENCRYPT);
}

// Function for generating RSA keys
RSA *generate_rsa_key() {
    BIGNUM *bne = BN_new();
    RSA *rsa = RSA_new();
    BN_set_word(bne, RSA_F4);
    RSA_generate_key_ex(rsa, RSA_KEY_LENGTH, bne, NULL);
    BN_free(bne);
    return rsa;
}

// Attack thread function
void *attack_thread(void *arg) {
    struct thread_data *data = (struct thread_data *)arg;
    time_t start_time = time(NULL);
    printf("Thread %d: Starting attack on %s:%d for %d seconds.\n", data->thread_id, data->ip, data->port, data->duration);

    while (difftime(time(NULL), start_time) < data->duration) {
        // Simulated attack logic
        printf("Thread %d: Attacking %s:%d\n", data->thread_id, data->ip, data->port);
        usleep(500000); // Simulate work (500ms delay)
    }

    printf("Thread %d: Attack finished.\n", data->thread_id);
    pthread_exit(NULL);
}

// Main function
int main(int argc, char *argv[]) {
    if (argc != 5) {
        printf("Usage: %s <IP> <PORT> <DURATION> <THREADS>\n", argv[0]);
        return 1;
    }

    if (check_expiry()) {
        return 1; // Exit if expired
    }

    char *ip = argv[1];
    int port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int threads = atoi(argv[4]);

    pthread_t thread_ids[threads];
    struct thread_data thread_args[threads];

    for (int i = 0; i < threads; i++) {
        strncpy(thread_args[i].ip, ip, sizeof(thread_args[i].ip) - 1);
        thread_args[i].port = port;
        thread_args[i].duration = duration;
        thread_args[i].thread_id = i + 1;

        if (pthread_create(&thread_ids[i], NULL, attack_thread, &thread_args[i]) != 0) {
            perror("Failed to create thread");
            return 1;
        }
    }

    for (int i = 0; i < threads; i++) {
        pthread_join(thread_ids[i], NULL);
    }

    printf("All threads finished.\n");
    return 0;
}
