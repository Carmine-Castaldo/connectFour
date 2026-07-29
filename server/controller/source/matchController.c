#include "../../game/connectFour.h"
#include "../header/connectionController.h"
#include <string.h>
#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#define MAX_MATCHES 50
#define status_waiting -1
#define status_game_on 0
#define status_terminated 1
#define p1_turn 0
#define p2_turn 1

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
    to_add.state = status_waiting;
    to_add.id_match = next_id_match++;

    if(i >= MAX_MATCHES)
        printf("Superato il numero di parite massimo\n");
    else{
        matches[i] = to_add;
        printf("Partita %d Creata\n", matches[i].id_match);
    }
    fflush(stdout);

    pthread_mutex_unlock(&mutex_match);
    return i < MAX_MATCHES;
}

int join_match_request(int id_match, int fd_applicant){
    pthread_mutex_lock(&mutex_match);
    int i = 0;
    printf("looking for match\n");
    while((i < MAX_MATCHES) && (matches[i].id_match != id_match)){
        i++;
        printf("%d\n", i);
    }
    if( i >= MAX_MATCHES)
        printf("Partita inesistente\n");
    else if(matches[i].state != status_waiting){
        printf("Partita terminata o in corso");
    }else{
        printf("Match found\n");
        matches[i].fd_giocatore2 = fd_applicant;
        matches[i].player2 = &fd_applicant;
        matches[i].state = status_game_on;
        matches[i].turn = p1_turn;
    }
    sleep(3);
    if(matches[i].state == status_game_on){
        printf("La partita: %d è iniziata\n", matches[i].id_match);
        printf("player1: %d player 2: %d\n", matches[i].fd_giocatore1, matches[i].fd_giocatore2);
    }

    pthread_mutex_unlock(&mutex_match);
}

int handle_msg(int client_socket, char * buffer){
    printf("HANDLING: %s\n", buffer);
    buffer[strcspn(buffer, "\r\n")] = '\0';
    fflush(stdout); 
    int id_match;
    if(strcmp(buffer, "CREATE") == 0)
        create_match(client_socket);
    else if(sscanf(buffer, "JOIN %d\n", &id_match) == 1){
        printf("Joining %d\n", id_match);
        join_match_request(id_match, client_socket);
    }
    else if(strcmp(buffer, "DISCONNECT") == 0)
        printf("DISCONNECT\n");
    else
        printf("COMANDO ERRATO\n");
}



void accept_or_reject_player(int match_id, int decision){}
void play_turn(int match_id, int column){}
void end_match(int match_id, int result){}
void reset_match(int match_id){}
//void broadcast_status(){}