#include <pthread.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "../header/connectionController.h"


int init_server(int port){

    int fd_server = socket(PF_INET,SOCK_STREAM, 0);
    if(fd_server == -1)
        perror("socket"), exit(1);
    

    struct sockaddr_in my_address;
    my_address.sin_family = AF_INET;
    my_address.sin_port = htons(port);
    my_address.sin_addr.s_addr = htonl(INADDR_ANY);
    
    if(bind( fd_server, (struct sockaddr *) &my_address, sizeof(my_address)) < 0)
        perror("bind"), exit(1);
    
    printf("waitng");
    int sd = listen(fd_server, 16);
    if(sd < 0)
        perror("listen"), exit(1);

    struct sockaddr client_addr; 
    socklen_t client_len;
    int connect_sd;
    while(1){
        client_len = sizeof(client_addr);
        connect_sd = accept(fd_server, (struct sockaddr *) &client_addr, &client_len);
        if(connect_sd < 0)
            perror("accept"), exit(1);
        
        int * new_sock = malloc(sizeof(int));
        *new_sock = connect_sd;
        pthread_t tid;

        if(pthread_create(&tid,NULL, handle_client, (void*) new_sock) < 0){
            perror("pthread_create");
            close(connect_sd);
            free(new_sock);
        }
        pthread_detach(tid);
    }
    return 0;
}

void *handle_client(void *client_server_socket){
    int client_socket = *(int*)client_server_socket;
    free(client_server_socket);

    //qui codice in cui riceve i messaggi per creare/partecipare/ecc... alle partite

    close(client_socket);
    pthread_exit(NULL);
}
void accept_connection(int server_socket){}
int send_msg(int client_socket, char *msg){}
int recv_msg(int client_socket, char *buffer){}