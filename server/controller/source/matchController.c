#include "../../game/connectFour.h"
#include "../header/connectionController.h"
#include "../header/matchController.h"
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
#define WINNER_P1 0
#define WINNER_P2 1
#define DRAW 2
int next_id_match = 0;
Match matches[MAX_MATCHES];
pthread_mutex_t mutex_match = PTHREAD_MUTEX_INITIALIZER;



Match* get_match(int client_fd) {
    for (int i = 0; i < MAX_MATCHES; i++) {
        if (matches[i].id_match != -1 && 
            (matches[i].fd_giocatore1 == client_fd || matches[i].fd_giocatore2 == client_fd)) {
            return &matches[i];
        }
    }
    return NULL;
}

int get_opponent(int current_client_fd) {
    int opp_fd = -1;

    pthread_mutex_lock(&mutex_match);

    for (int i = 0; i < MAX_MATCHES; i++) {
        if (matches[i].state == status_game_on) {
            if (matches[i].fd_giocatore1 == current_client_fd) {
                opp_fd = matches[i].fd_giocatore2;
                break;
            } else if (matches[i].fd_giocatore2 == current_client_fd) {
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

Match * get_match_by_Id(int id_match){
    int i = 0;
    while( (i < MAX_MATCHES) && (matches[i].id_match != id_match)) i++;
    if( i >= MAX_MATCHES) return NULL;
    else return &matches[i];
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

void init_match(Match *match, int id_match, int fd_creator) {
    match->id_match = id_match;
    match->fd_giocatore1 = fd_creator;
    match->fd_giocatore2 = -1;
    match->moves = 0;
    match->player1 = &(match->fd_giocatore1);
    match->player2 = NULL;
    match->state = status_waiting;
    match->join_status = 0;
    match->p1_rematch = 0;
    match->p2_rematch = 0;
    memset(match->grid, 0, sizeof(match->grid));
    pthread_cond_init(&match->cond_join, NULL);
}

int create_match(int fd_creator) {
    pthread_mutex_lock(&mutex_match);

    int i = 0, toReturn = -1;
    while ((i < MAX_MATCHES) && (matches[i].id_match != -1)) i++;

    if (i >= MAX_MATCHES)
        printf("TOO MANY MATCHES\n");
    else {
        init_match(&matches[i], next_id_match++, fd_creator);
        toReturn = matches[i].id_match;
    }

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
        matches[i].player2 = &(matches[i].fd_giocatore2);
        matches[i].state = status_game_on;
        matches[i].turn = p1_turn;
        toReturn = 1;
    }
    
    pthread_mutex_unlock(&mutex_match);
    return toReturn;

}

void end_match(Match * match, int result){
    int winner = -1, looser = -1;
    char msg[64];
    if(result == 0){
        winner = match->fd_giocatore1;
        looser = match->fd_giocatore2;
        send_msg(winner, "WIN");
        send_msg(looser, "LOSE");
    }else if(result == 1){
        winner = match->fd_giocatore2;
        looser = match->fd_giocatore1;
        send_msg(looser, "LOSE");
        send_msg(winner, "WIN");
    }else{
        send_msg(match->fd_giocatore1, "DRAW");
        send_msg(match->fd_giocatore2, "DRAW");
    }
    match->state = status_terminated;

    snprintf(msg, sizeof(msg), "THE GAME %d IS OVER", match->id_match);
    broadcast(msg);   
}

void reset_match(int match_id) {
    pthread_mutex_lock(&mutex_match);
    for (int i = 0; i < MAX_MATCHES; i++) {
        if (matches[i].id_match == match_id) {
            pthread_cond_destroy(&matches[i].cond_join);
            matches[i].state = -1; 
            matches[i].id_match = -1;
            matches[i].fd_giocatore1 = -1;
            matches[i].fd_giocatore2 = -1;
            matches[i].moves = 0;
            matches[i].turn = 0;
            memset(matches[i].grid, 0, sizeof(matches[i].grid)); 
            matches[i].player1 = NULL;
            matches[i].player2 = NULL;
            break;
        }
    }
    pthread_mutex_unlock(&mutex_match);
}

int play_turn(int match_id, int col){
    pthread_mutex_lock(&mutex_match);
    int i = 0;
    int inserted_row = -1;
    while((i < MAX_MATCHES) && (matches[i].id_match != match_id)) i++;
    if(i >= MAX_MATCHES)
        printf("MATCH %d DOES NOT EXISTS\n", match_id);
    else{
        inserted_row = insertDisc(&matches[i], col, matches[i].turn + 1);
        if(matches[i].turn == 0)
            matches[i].turn = 1;
        else
            matches[i].turn = 0;
    }
    pthread_mutex_unlock(&mutex_match);
    return inserted_row;
}

void handle_client_disconnect(int client_socket) {
    pthread_mutex_lock(&mutex_match);
    Match * match = get_match(client_socket);
    if (match != NULL) {
       int opp = (match->fd_giocatore1 == client_socket) ? match->fd_giocatore2 : match->fd_giocatore1;
       if (match->state == status_game_on) {
           if (opp != -1) 
           send_msg(opp, "OPPONENT_DISCONNECTED");
           char msg[64];
           snprintf(msg, sizeof(msg), "THE GAME %d IS OVER", match->id_match);
           broadcast(msg);
        } 
        pthread_mutex_unlock(&mutex_match);
        reset_match(match->id_match);
    }else
        pthread_mutex_unlock(&mutex_match);
}

int request_to_creator(int id_match, int client_req) {
    pthread_mutex_lock(&mutex_match);
    Match *match = get_match_by_Id(id_match);
    if (match == NULL || match->state != status_waiting) {
        pthread_mutex_unlock(&mutex_match);
        return 0; 
    }
    match->join_status = 0;
    match->fd_giocatore2 = client_req;
    
    char msg[64];
    snprintf(msg, sizeof(msg), "JOIN_REQUEST %d", client_req);
    send_msg(match->fd_giocatore1, msg);
    snprintf(msg, sizeof(msg), "ROOM %d IS BUSY", id_match);
    broadcast_except(msg, client_req);
    
    while (match->join_status == 0) 
        pthread_cond_wait(&match->cond_join, &mutex_match); 
    
    int result = (match->join_status == 1) ? 1 : 0;
    
    if (result == 0) {
        match->fd_giocatore2 = -1;
        snprintf(msg, sizeof(msg), "ROOM %d IS AVAILABLE", id_match);
        broadcast(msg);
    }
    pthread_mutex_unlock(&mutex_match);
    return result;
}

int handle_msg(int client_socket, char *buffer) {
    buffer[strcspn(buffer, "\r\n")] = '\0';
    printf("HANDLING: %s\n", buffer);
    fflush(stdout); 
    int id_match, col, player;
    if (strcmp(buffer, "CREATE") == 0) 
        handle_create(client_socket);
    else if (sscanf(buffer, "JOIN %d", &id_match) == 1) 
        handle_join(client_socket, id_match);
    else if (sscanf(buffer, "MOVE %d ", &col) >= 1) 
        handle_move(client_socket, col);
    else if (strncmp(buffer, "QUIT", 4) == 0)
        handle_quit(client_socket);
    else if (strcmp(buffer, "DISCONNECT") == 0) {
        handle_client_disconnect(client_socket);
        return -1;
    }else if( strcmp(buffer, "ACCEPT") == 0)
        handle_accept(client_socket);
    else if( strcmp(buffer, "REJECT") == 0)
        handle_reject(client_socket);
    else if (strcmp(buffer, "REMATCH_ACCEPT") == 0)
        handle_rematch_accept(client_socket);
    else if (strcmp(buffer, "REMATCH_DECLINE") == 0) {
        handle_rematch_declined(client_socket);
    }else
        printf("%s\n",buffer);

    return 0;
}

void handle_join(int client_socket, int id_match) {
    if (request_to_creator(id_match, client_socket)) {
        if (join_match_request(id_match, client_socket)) {
            int fd_creator = get_opponent_fd(id_match, client_socket);
            if (fd_creator != -1) {
                send_msg(fd_creator, "YOUR TURN");   
                send_msg(client_socket, "WAIT TURN");
                char msg[64];
                snprintf(msg, sizeof(msg), "THE MATCH %d IS STARTING", id_match);
                broadcast(msg);
            }
        }else 
            send_msg(client_socket, "ERROR IMPOSSIBLE TO JOIN THE MATCH\n");
    }else 
        send_msg(client_socket, "JOIN REJECTED\n");
}

void handle_create(int client_socket) {
    printf("HANDLING CREATE\n");
    int match_id = create_match(client_socket);
    if(match_id != -1){
        char msg[64];
        snprintf(msg, sizeof(msg), "THE MATCH %d IS CREATED, JOIN!!", match_id);
        broadcast(msg);
        send_msg(client_socket, "WAIT TURN");
    }else
        send_msg(client_socket, "THE SERVER IS BUSY");
    
}

void handle_move(int client_socket, int col){
    Match * match = get_match(client_socket);
    int id_opp = get_opponent(client_socket); 
    if (id_opp != -1 && match != NULL && match->state == status_game_on){
        fflush(stdout);
        int row = play_turn(match->id_match, col);
        pthread_mutex_lock(&mutex_match);
        int player_num = (match->fd_giocatore1 == client_socket) ? 1 : 2;
        char msg[64];
        snprintf(msg, sizeof(msg), "UPDATE_BOARD %d %d %d", player_num, row, col);
        send_msg(client_socket, msg);
        send_msg(id_opp, msg);
        usleep(1000);
        
        if (check_win(match, col)) 
            end_match(match, (client_socket == match->fd_giocatore1) ? WINNER_P1 : WINNER_P2);
        else if (check_draw(match)) 
            end_match(match, DRAW);
        else {
            send_msg(client_socket, "WAIT TURN");
            send_msg(id_opp, "YOUR TURN");
        }
        pthread_mutex_unlock(&mutex_match);
    } else
        printf("ILLEGAL MOVE\n"); 
}

void handle_quit(int client_socket){
    pthread_mutex_lock(&mutex_match);
    Match *match = get_match(client_socket);
    if (match != NULL) {
        int id_match = match->id_match;
        if (match->state != status_waiting) {
            int id_opp = (match->fd_giocatore1 == client_socket) ? match->fd_giocatore2 : match->fd_giocatore1;
            if (id_opp != -1)
                send_msg(id_opp, "OPPONENT_DISCONNECTED");
        }
        char msg[64];
        snprintf(msg, sizeof(msg), "THE GAME %d IS OVER", id_match);
        broadcast(msg);
        
        pthread_mutex_unlock(&mutex_match);
        reset_match(id_match);
    } else {
        pthread_mutex_unlock(&mutex_match);
        printf("QUIT: MATCH NOT FOUND FOR CLIENT %d\n", client_socket);  
    }
}

void handle_accept(int client_socket) {
    pthread_mutex_lock(&mutex_match);
    Match *match = NULL;
    for (int i = 0; i < MAX_MATCHES; i++) {
        if (matches[i].id_match != -1 && 
            matches[i].fd_giocatore1 == client_socket && 
            matches[i].fd_giocatore2 != -1 && 
            matches[i].join_status == 0) {
            match = &matches[i];
            break;
        }
    }
    if (match != NULL) {
        match->join_status = 1; 
        pthread_cond_signal(&match->cond_join);
    }  
    pthread_mutex_unlock(&mutex_match);
}

void handle_reject(int client_socket) {
    pthread_mutex_lock(&mutex_match);
    Match *match = NULL;
    for (int i = 0; i < MAX_MATCHES; i++) {
        if (matches[i].id_match != -1 && 
            matches[i].fd_giocatore1 == client_socket && 
            matches[i].fd_giocatore2 != -1 && 
            matches[i].join_status == 0) {
            match = &matches[i];
            break;
        }
    }
    if (match != NULL) {
        match->join_status = 2; 
        pthread_cond_signal(&match->cond_join);
    }  
    pthread_mutex_unlock(&mutex_match);
}

void handle_rematch_accept(int client_socket){
    pthread_mutex_lock(&mutex_match);
    Match * match = get_match(client_socket);
    if (match != NULL) {
        printf("HERE 1");
        if (match->state == status_terminated) {
            printf("HERE 2");
            int opp = (match->fd_giocatore1 == client_socket) ? match->fd_giocatore2 : match->fd_giocatore1;
            if (client_socket == match->fd_giocatore1)
                match->p1_rematch = 1;
            else
                match->p2_rematch = 1;
            
            if (match->p1_rematch == 1 && match->p2_rematch == 1) 
                restart_match(match);
            else if (opp != -1) 
                send_msg(opp, "OPPONENT_WANTS_REMATCH"); 
            printf("HERE 3");
        }
    }
    printf("HERE 4");
    pthread_mutex_unlock(&mutex_match);
}

void handle_rematch_declined(int client_socket){
    pthread_mutex_lock(&mutex_match);
    Match *match = get_match(client_socket);
    
    if (match != NULL) {
        int opp = (match->fd_giocatore1 == client_socket) ? match->fd_giocatore2 : match->fd_giocatore1;
        int id_match = match->id_match;

        if (opp != -1) {
            send_msg(opp, "REMATCH_DECLINED");
        }
        pthread_mutex_unlock(&mutex_match);
        reset_match(id_match);
    } else 
        pthread_mutex_unlock(&mutex_match);
    
}

void restart_match(Match * match){
    memset(match->grid, 0, sizeof(match->grid));
    match->moves = 0;
    match->state = status_game_on;
    match->p1_rematch = 0;
    match->p2_rematch = 0;
    match->turn = p1_turn;

    send_msg(match->fd_giocatore1, "REMATCH_START");
    send_msg(match->fd_giocatore2, "REMATCH_START");
    
    send_msg(match->fd_giocatore1, "YOUR TURN");
    send_msg(match->fd_giocatore2, "WAIT TURN");
}
