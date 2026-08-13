#include <pthread.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include "../header/connectionController.h"
#include "../header/matchController.h"

#define MAX_CLIENT 100
int clients[MAX_CLIENT];
int next_client = 0;
pthread_mutex_t mutex_clients = PTHREAD_MUTEX_INITIALIZER;

int init_server(int port){
    for(int i = 0; i < MAX_CLIENT; i++)
        clients[i] = -1;
    
    int fd_server = socket(PF_INET,SOCK_STREAM, 0);
    int opt = 1;
    if(fd_server == -1)
        perror("socket failed"), exit(1);
    
    if (setsockopt(fd_server, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0)
        perror("setsockopt failed"), exit(EXIT_FAILURE); 
    

    struct sockaddr_in my_address;
    my_address.sin_family = AF_INET;
    my_address.sin_port = htons(port);
    my_address.sin_addr.s_addr = htonl(INADDR_ANY);
    
    if(bind( fd_server, (struct sockaddr *) &my_address, sizeof(my_address)) < 0)
        perror("bind failed"), exit(1);
    
    int sd = listen(fd_server, 16);

    if(sd < 0)
        perror("listen failed"), exit(1);

    
    accept_connection(fd_server);

    return 0;
}

int get_next_client(){
    int i = 0;
    while( i < MAX_CLIENT && clients[i] != -1) i++;
    if(i >= MAX_CLIENT) i = -1;
    return i;
}

void *handle_client(void *client_server_socket) {

    int client_socket = *(int*)client_server_socket;
    free(client_server_socket);
    char buffer[1024];
    
    while (1) {
        memset(buffer, 0, sizeof(buffer));

        int letti = recv_msg(client_socket, buffer);
    
        if (letti <= 0) {
            printf("HANDLE DISCONNECTION OF %d\n", client_socket);
            handle_client_disconnect(client_socket);
            break; 
        }

        buffer[letti] = '\0';

        int res = handle_msg(client_socket, buffer);
        if (res < 0) 
            break;
        
    }
    close(client_socket); 
    pthread_exit(NULL);   
}

void accept_connection(int server_socket){
    struct sockaddr_in client_addr; 
    socklen_t client_len;
    int connect_sd;
    
    while(1){
        client_len = sizeof(client_addr);
        connect_sd = accept(server_socket, (struct sockaddr *) &client_addr, &client_len);
        
        if(connect_sd < 0) {
            perror("accept");
            continue; 
        }
        
        pthread_mutex_lock(&mutex_clients);
        int next_client_pos = get_next_client();
        
        if (next_client_pos == -1) {
            pthread_mutex_unlock(&mutex_clients);
            printf("Too many connection, the server is full, client rejected: %d\n", connect_sd);
            send_msg(connect_sd, "ERROR_SERVER_FULL");
            close(connect_sd);
            continue;
        }
        
        clients[next_client_pos] = connect_sd;
        pthread_mutex_unlock(&mutex_clients);
        
        int *new_sock = malloc(sizeof(int));
        *new_sock = connect_sd;
        pthread_t tid;

        if(pthread_create(&tid, NULL, handle_client, (void*) new_sock) < 0){
            perror("pthread_create");
            
            pthread_mutex_lock(&mutex_clients);
            clients[next_client_pos] = -1;
            pthread_mutex_unlock(&mutex_clients);
            
            close(connect_sd);
            free(new_sock);
        } else
            pthread_detach(tid);
        
    }
}

int send_msg(int client_socket, char *msg){
    char buffer[512];
    snprintf(buffer, sizeof(buffer), "%s\n", msg); 
    
    return write(client_socket, buffer, strlen(buffer)); 
}

int recv_msg(int client_socket, char *buffer){

    int n_bytes = read(client_socket, buffer, 1024); 
    if (n_bytes > 0) 
        buffer[n_bytes] = '\0';
    
    return n_bytes;
}


void broadcast(char * msg){
    pthread_mutex_lock(&mutex_clients);

        for(int i = 0; i < MAX_CLIENT; i++)
            if(clients[i] != -1)
                send_msg(clients[i], msg);
        
    pthread_mutex_unlock(&mutex_clients);
}

void broadcast_except(char * msg, int excluded_socket) {
    pthread_mutex_lock(&mutex_clients);
    for (int i = 0; i < MAX_CLIENT; i++) 
        if (clients[i] != -1 && clients[i] != excluded_socket) 
            send_msg(clients[i], msg);
        
    pthread_mutex_unlock(&mutex_clients);
}