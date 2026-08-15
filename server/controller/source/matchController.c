#include "../../game/connectFour.h"
#include "../header/connectionController.h"
#include "../header/matchController.h"
#include <string.h>
#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>

#define MAX_MATCHES 50
#define status_waiting -1
#define status_game_on 0
#define status_terminated 1
#define status_connecting 2
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

int get_opponent(int client_socket) {
    int opp_fd = -1;

    pthread_mutex_lock(&mutex_match);
    Match * match = get_match(client_socket);
    if(match != NULL)
        opp_fd = (match->fd_giocatore1 == client_socket) ? match->fd_giocatore2 : match->fd_giocatore1;
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

int join_match_request(int id_match, int client_applicant){
    pthread_mutex_lock(&mutex_match);
    int toReturn = 0;
    int i = 0;
    printf("looking for match\n");
    while((i < MAX_MATCHES) && (matches[i].id_match != id_match))
        i++;
    if( i >= MAX_MATCHES)
        printf("Partita inesistente\n");
    else if(matches[i].state != status_waiting && matches[i].state != status_connecting){
        printf("Partita terminata o in corso\n");
    } else {
        printf("Match found\n");
        matches[i].fd_giocatore2 = client_applicant;
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
    printf("MSG: %s\n", msg); 
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


int request_to_creator(int id_match, int client_req) {
    pthread_mutex_lock(&mutex_match);
    Match *match = get_match_by_Id(id_match);
    if (match == NULL || match->state != status_waiting) {
        pthread_mutex_unlock(&mutex_match);
        return 0;
    }

    match->join_status = 0;
    match->fd_giocatore2 = client_req;
    match->state = status_connecting;
    
    char msg[64];
    snprintf(msg, sizeof(msg), "JOIN_REQUEST %d", client_req);
    send_msg(match->fd_giocatore1, msg);
    
    snprintf(msg, sizeof(msg), "ROOM %d CONNECTING", id_match);
    broadcast_except(msg, match->fd_giocatore1);

    while (match->join_status == 0)
        pthread_cond_wait(&match->cond_join, &mutex_match);

    int final_status = match->join_status;

    if (final_status != 1 && final_status != 3) {
        match->state = status_waiting;
        match->fd_giocatore2 = -1;
    }
    pthread_mutex_unlock(&mutex_match);

    if (final_status == 1)
        return 1; 
    else if (final_status == 3) {
        send_msg(client_req, "JOIN_REJECTED Creator Disconnected");
        char msg_over[64];
        snprintf(msg_over, sizeof(msg_over), "THE GAME %d IS OVER", id_match);
        broadcast(msg_over);
        reset_match(id_match);
        return 0;
    } else {
        send_msg(client_req, "JOIN_REJECTED");
        char msg_avail[64];
        snprintf(msg_avail, sizeof(msg_avail), "ROOM %d AVAILABLE", id_match);
        broadcast(msg_avail);
        return 0;
    }
}

int play_turn(Match * match, int col){
    pthread_mutex_lock(&mutex_match);
    int i = 0;
    int inserted_row = -1;
    if(match != NULL){
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
    Match *match = get_match(client_socket);
    
    if (match != NULL) {
        int opp = (match->fd_giocatore1 == client_socket) ? match->fd_giocatore2 : match->fd_giocatore1;
        
        if (match->state == status_game_on || match->state == status_terminated) {
            if (opp != -1) 
                send_msg(opp, "OPPONENT_DISCONNECTED");
            char msg[64];
            snprintf(msg, sizeof(msg), "THE GAME %d IS OVER", match->id_match);
            broadcast(msg);
            
            pthread_mutex_unlock(&mutex_match);
            reset_match(match->id_match); 
        } 
        else if (match->state == status_waiting || match->state == status_connecting) {
            if (client_socket == match->fd_giocatore1) { 
                if (match->state == status_connecting && match->join_status == 0) {
                    match->join_status = 3; 
                    pthread_cond_signal(&match->cond_join);
                    pthread_mutex_unlock(&mutex_match);
                } else {
                    char msg[64];
                    snprintf(msg, sizeof(msg), "THE GAME %d IS OVER", match->id_match);
                    broadcast(msg);
                    pthread_mutex_unlock(&mutex_match);
                    reset_match(match->id_match);
                }
            } else { 
                if (match->state == status_connecting && match->join_status == 0) {
                    send_msg(match->fd_giocatore1, "JOIN_CANCELLED");
                    
                    match->join_status = 2; 
                    match->state = status_waiting;
                    match->fd_giocatore2 = -1;
                    pthread_cond_signal(&match->cond_join);
                    
                    char msg[64];
                    snprintf(msg, sizeof(msg), "ROOM %d AVAILABLE", match->id_match);
                    broadcast(msg);
                } else {
                    match->fd_giocatore2 = -1;
                }
                pthread_mutex_unlock(&mutex_match);
            }
        } else
            pthread_mutex_unlock(&mutex_match);
        
    } else
        pthread_mutex_unlock(&mutex_match);
    
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
        if (send_msg(client_socket, "WAIT TURN") <= 0) {
            printf("Lo sfidante e' disconnesso, il creatore vince a tavolino!\n");
            pthread_mutex_lock(&mutex_match);
            Match *match = get_match_by_Id(id_match);
            if (match != NULL) {
                end_match(match, 0); 
            }
            pthread_mutex_unlock(&mutex_match);
            return;
        }
        if (join_match_request(id_match, client_socket)) {
            int fd_creator = get_opponent(client_socket);
            if (fd_creator != -1) {
                send_msg(fd_creator, "YOUR TURN");   
                char msg[64];
                snprintf(msg, sizeof(msg), "THE MATCH %d IS STARTING", id_match);
                broadcast(msg);
            }
        }
    }
}
void handle_create(int client_socket) {
    printf("HANDLING CREATE\n");
    for(int i = 0; i < MAX_MATCHES; i++){
        if(matches[i].id_match != -1){
            printf("MATCH %d \n", matches[i].id_match);
        }
    }
    int match_id = create_match(client_socket);
    if(match_id != -1){
        char msg[64];
        snprintf(msg, sizeof(msg), "THE MATCH %d IS CREATED", match_id);
        broadcast(msg);
        send_msg(client_socket, "WAIT TURN");
    }else
        send_msg(client_socket, "THE SERVER IS BUSY");
    
}

void handle_move(int client_socket, int col){
    Match * match = get_match(client_socket);
    if (match != NULL && match->state == status_game_on){
        int opp = (match->fd_giocatore1 == client_socket) ? match->fd_giocatore2 : match->fd_giocatore1;
        fflush(stdout);
        if(opp != -1){
            int row = play_turn(match, col);
            pthread_mutex_lock(&mutex_match);
            int player_num = (match->fd_giocatore1 == client_socket) ? 1 : 2;
            char msg[64];
            snprintf(msg, sizeof(msg), "UPDATE_BOARD %d %d %d", player_num, row, col);
            send_msg(client_socket, msg);
            send_msg(opp, msg);
            usleep(1000);
            if (check_win(match, col)) 
                end_match(match, (client_socket == match->fd_giocatore1) ? WINNER_P1 : WINNER_P2);
            else if (check_draw(match)) 
                end_match(match, DRAW);
            else {
                send_msg(client_socket, "WAIT TURN");
                send_msg(opp, "YOUR TURN");
            }
            pthread_mutex_unlock(&mutex_match);
        }
        
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
        pthread_mutex_unlock(&mutex_match);
        broadcast(msg);
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
        if (match->state == status_terminated) {
            int opp = (match->fd_giocatore1 == client_socket) ? match->fd_giocatore2 : match->fd_giocatore1;

            if (client_socket == match->fd_giocatore1)
                match->p1_rematch = 1;
            else
                match->p2_rematch = 1;
            
            if (match->p1_rematch == 1 && match->p2_rematch == 1) 
                restart_match(match);
            else if (opp != -1) 
                send_msg(opp, "OPPONENT_WANTS_REMATCH"); 
        }
    }
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


void send_all_matches_to_client(int client_socket) {
    pthread_mutex_lock(&mutex_match);
    printf("SENDING MATCHES to %d\n", client_socket);
    for (int i = 0; i < MAX_MATCHES; i++) {
        if (matches[i].id_match != -1) {
            printf("SENDING MATCH %d\n", matches[i].id_match);
            char msg[64];
            const char *state_str = "";
            if (matches[i].state == status_game_on) 
                state_str = "PLAYING";
            else if (matches[i].state == status_terminated) 
                state_str = "TERMINATED";
            else if (matches[i].state == status_waiting)
                state_str = "AVAILABLE";
            else
                state_str = "CONNECTING";

            snprintf(msg, sizeof(msg), "ROOM %d %s", matches[i].id_match, state_str);
            send_msg(client_socket, msg);
        }
    }
    
    pthread_mutex_unlock(&mutex_match);
}