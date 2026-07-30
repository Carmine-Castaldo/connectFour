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
#define p1_turn 1
#define p2_turn 2

int next_id_match = 0;
Match matches[MAX_MATCHES];
pthread_mutex_t mutex_match = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t mutex_match_on = PTHREAD_MUTEX_INITIALIZER;

int get_match_and_opponent(int current_client_fd, int *out_match_id) {
    int opp_fd = -1;
    *out_match_id = -1;

    pthread_mutex_lock(&mutex_match);

    for (int i = 0; i < MAX_MATCHES; i++) {
        if (matches[i].state == status_game_on) {
            if (matches[i].fd_giocatore1 == current_client_fd) {
                *out_match_id = matches[i].id_match;
                opp_fd = matches[i].fd_giocatore2;
                break;
            } else if (matches[i].fd_giocatore2 == current_client_fd) {
                *out_match_id = matches[i].id_match;
                opp_fd = matches[i].fd_giocatore1;
                break;
            }
        }
    }

    pthread_mutex_unlock(&mutex_match);
    return opp_fd;
}

int get_opponent_fd(int id_match, int current_client_fd) {
    int opp_fd = -1;

    pthread_mutex_lock(&mutex_match); 

    for (int i = 0; i < MAX_MATCHES; i++) 
        if (matches[i].id_match == id_match && matches[i].state == status_game_on) {
            if (matches[i].fd_giocatore1 == current_client_fd)
                opp_fd = matches[i].fd_giocatore2;
            else if (matches[i].fd_giocatore2 == current_client_fd) 
                opp_fd = matches[i].fd_giocatore1;
            
            break;
        }
    

    pthread_mutex_unlock(&mutex_match); 

    return opp_fd;
}


int init_matchController(){
    Match match;
    match.id_match = -1;
    for(int i = 0; i < 6; i++)
        for(int j = 0; j < 7; j++)
            match.grid[i][j] = 0;
    
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

    int i = 0, toReturn = -1;
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
        memset(to_add.grid, 0, sizeof(to_add.grid));
        matches[i] = to_add;
        toReturn = matches[i].id_match;
        printf("Partita %d Creata\n", matches[i].id_match);
    }
    fflush(stdout);

    pthread_mutex_unlock(&mutex_match);
    return toReturn;
}

int join_match_request(int id_match, int fd_applicant){
    pthread_mutex_lock(&mutex_match);
    int toReturn = 0;
    int i = 0;
    printf("looking for match\n");
    while((i < MAX_MATCHES) && (matches[i].id_match != id_match))
        i++;
    if( i >= MAX_MATCHES)
        printf("Partita inesistente\n");
    else if(matches[i].state != status_waiting){
        printf("Partita terminata o in corso\n");
    }else{
        printf("Match found\n");
        matches[i].fd_giocatore2 = fd_applicant;
        matches[i].player2 = &fd_applicant;
        matches[i].state = status_game_on;
        matches[i].turn = p1_turn;
        toReturn = 1;
    }
    
    pthread_mutex_unlock(&mutex_match);
    return toReturn;

}

void accept_or_reject_player(int match_id, int decision){}

void end_match(Match * match, int result){
    if(result == 0){
        send_msg(matches->fd_giocatore1, "WIN");
        send_msg(matches->fd_giocatore2, "LOSE");
    }else if(result == 1){
        send_msg(matches->fd_giocatore1, "LOSE");
        send_msg(matches->fd_giocatore2, "WIN");
    }else{
        send_msg(matches->fd_giocatore1, "DRAW");
        send_msg(matches->fd_giocatore2, "DRAW");
    }
}
void reset_match(int match_id) {
    pthread_mutex_lock(&mutex_match);
    for (int i = 0; i < MAX_MATCHES; i++) {
        if (matches[i].id_match == match_id) {
            matches[i].state = -1; 
            matches[i].fd_giocatore1 = -1;
            matches[i].fd_giocatore2 = -1;
            matches[i].moves = 0;
            matches[i].turn = 0;
            memset(matches[i].grid, 0, sizeof(matches[i].grid)); 
            break;
        }
    }
    pthread_mutex_unlock(&mutex_match);
}
//void broadcast_status(){}

int play_turn(int match_id, int col){
    pthread_mutex_lock(&mutex_match_on);
    int i = 0;
    int inserted_row = -1;
    while((i < MAX_MATCHES) && (matches[i].id_match != match_id)) i++;
    if(i >= MAX_MATCHES)
        printf("Partita Inesistente\n");
    else{
        printf("Inserting disc \n");
        inserted_row = insertDisc(&matches[i], col, matches[i].turn + 1);
        if(matches[i].turn == 0)
            matches[i].turn = 1;
        else
            matches[i].turn = 0;
    }
    pthread_mutex_unlock(&mutex_match_on);
    return inserted_row;
}
int handle_msg(int client_socket, int *current_match_id, char *buffer) {
    buffer[strcspn(buffer, "\r\n")] = '\0';
    printf("HANDLING: %s\n", buffer);
    fflush(stdout); 

    int id_match, col, player;

    if (strcmp(buffer, "CREATE") == 0) {
        *current_match_id = create_match(client_socket);
        printf("FD_CREATOR %d\n", client_socket);
        if (*current_match_id != -1) 
            send_msg(client_socket,"WAIT TURN");
        
    }
    else if (sscanf(buffer, "JOIN %d", &id_match) == 1) {
        printf("Joining %d\n", id_match);
        if (join_match_request(id_match, client_socket)) {
            *current_match_id = id_match;
            int fd_creator = get_opponent_fd(id_match, client_socket);
            printf("FD_OPPONENT IN JOIN: %d, FD_JOINER: %d\n", fd_creator, client_socket);
            if (fd_creator != -1) {
                send_msg(fd_creator, "YOUR TURN");   
                send_msg(client_socket, "WAIT TURN");
            }
        }else 
            send_msg(client_socket, "ERROR Impossibile unirsi alla partita\n");
        
    }
    else if (sscanf(buffer, "MOVE %d ", &col) >= 1) {
        
        int id_match = -1;
        int id_opp = get_match_and_opponent(client_socket, &id_match); 
        printf("Move in col: %d in match: %d\n", col, id_match);
        printf("FD_OPPONENT: %d, FD_MOVER: %d\n", id_opp, client_socket);
        if (id_opp != -1 && id_match != -1){
                fflush(stdout);
                int row = play_turn(id_match, col);
                int player_num = (matches[id_match].fd_giocatore1 == client_socket) ? 1 : 2;
                char msg[100];

                snprintf(msg, sizeof(msg), "UPDATE_BOARD %d %d %d", player_num, row, col);
                send_msg(client_socket, msg);
                send_msg(id_opp, msg);
                usleep(1000);
                 if (check_win(&matches[id_match], col)) {
                    printf("MATCH: %d WINNER: %d\n", id_match, client_socket);
                    send_msg(client_socket, "WIN");  
                    send_msg(id_opp, "LOSE");        
                    matches[id_match].state = status_terminated;
                    reset_match(id_match);
                } 
                else if (check_draw(&matches[id_match])) {
                    printf("DRAW\n", id_match);
                    send_msg(client_socket, "DRAW");
                    send_msg(id_opp, "DRAW");
                    matches[id_match].state = status_terminated;
                    reset_match(id_match);
                } 
                else {
                    send_msg(client_socket, "WAIT TURN");
                    send_msg(id_opp, "YOUR TURN");
                }

        }else 
            printf("ERRORE MOVE\n");
    
        
    }
    else if (strcmp(buffer, "DISCONNECT") == 0) {
        printf("DISCONNECT\n");
    }
    else {
        printf("COMANDO ERRATO\n");
    }

    return 0;
}
