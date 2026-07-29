#include "../../game/connectFour.h"
#include "../header/connectionController.h"
#include <string.h>
#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#define MAX_MATCHES 50

int next_id_match = 0;
Match matches[MAX_MATCHES];
pthread_mutex_t mutex_match = PTHREAD_MUTEX_INITIALIZER;

int init_matchController(){
    Match match;
    match.id_match = -1;
    for(int i = 0; i < MAX_MATCHES; i++)
        matches[i] = match;

    return 0;
}

int handle_quit(int client_socket){
    //rimuovere il giocatore dalla partita e terminare la partita
}

int create_match(int fd_creator){
 
    fflush(stdout);
    pthread_mutex_lock(&mutex_match);

    int i = 0;
    while ((i < MAX_MATCHES) && (matches[i].id_match != -1)) i++;

    Match to_add;
    to_add.fd_giocatore1 = fd_creator;
    to_add.fd_giocatore2 = -1;
    to_add.moves = 0;
    to_add.player1 = &fd_creator;
    to_add.player2 = NULL;
    to_add.state = -1;
    to_add.id_match = next_id_match++;

    if(i >= MAX_MATCHES)
        printf("Superato il numero di parite massimo\n");
    else{
        matches[i] = to_add;
        printf("Partita Creata\n");
    }
    fflush(stdout);

    pthread_mutex_unlock(&mutex_match);
    return i < MAX_MATCHES;
}

int handle_msg(int client_socket, char * buffer){
    
    buffer[strcspn(buffer, "\r\n")] = '\0';
    fflush(stdout); 

    printf("HANDLING: %s\n", buffer); 

    if(strcmp(buffer, "CREATE") == 0)
        create_match(client_socket);
    else if(strcmp(buffer, "DISCONNECT") == 0)
        printf("DISCONNECT");
    else
        printf("COMANDO ERRATO ");
}

int join_match_request(int match_id, int fd_applicant){}
void accept_or_reject_player(int match_id, int decision){}
void play_turn(int match_id, int column){}
void end_match(int match_id, int result){}
void reset_match(int match_id){}
//void broadcast_status(){}