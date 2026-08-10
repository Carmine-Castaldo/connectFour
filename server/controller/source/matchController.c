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


int create_match(int fd_creator){
    fflush(stdout);
    pthread_mutex_lock(&mutex_match);

    int i = 0, toReturn = -1;
    while ((i < MAX_MATCHES) && (matches[i].id_match != -1)) i++;

    if(i >= MAX_MATCHES) {
        printf("Superato il numero di partite massimo\n");
    } else {
        Match to_add;
        // TODO  costruttore
        to_add.fd_giocatore1 = fd_creator;
        to_add.fd_giocatore2 = -1;
        to_add.moves = 0;
        to_add.player1 = NULL; 
        to_add.player2 = NULL;
        to_add.state = status_waiting;
        to_add.id_match = next_id_match++;
        to_add.join_status = 0;
        to_add.p1_rematch = 0;
        to_add.p2_rematch = 0;
        pthread_cond_init(&to_add.cond_join, NULL);
        memset(to_add.grid, 0, sizeof(to_add.grid));
        matches[i] = to_add;
        matches[i].player1 = &(matches[i].fd_giocatore1);
        toReturn = matches[i].id_match;
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
    char msg[100];
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
    if(winner != -1)
        snprintf(msg, sizeof(msg), "THE GAME %d IS OVER, WINNER: %d LOOSER: %d", match->id_match, winner, looser);
    else
        snprintf(msg, sizeof(msg), "THE GAME %d IS OVER, IT'S A DRAW", match->id_match);

    broadcast(msg, match->fd_giocatore1, match->fd_giocatore2);   
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

//void broadcast_status(){}

int play_turn(int match_id, int col){
    pthread_mutex_lock(&mutex_match);
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
    pthread_mutex_unlock(&mutex_match);
    return inserted_row;
}

void handle_client_exit(int client_socket) {
    int id_match = -1;
    int id_opp = -1;
    int state = -1;
    pthread_mutex_lock(&mutex_match);
    for (int i = 0; i < MAX_MATCHES; i++) {
        if (matches[i].fd_giocatore1 == client_socket) {
            id_match = matches[i].id_match;
            id_opp = matches[i].fd_giocatore2;
            state = matches[i].state;
            break;
        } else if (matches[i].fd_giocatore2 == client_socket) {
            id_match = matches[i].id_match;
            id_opp = matches[i].fd_giocatore1;
            state = matches[i].state;
            break;
        }
    }
    pthread_mutex_unlock(&mutex_match);

    if (id_match != -1) {
        Match *match = get_match_by_Id(id_match);
        if (match != NULL) {
            if (state == status_game_on && id_opp != -1) {
                send_msg(id_opp, "OPPONENT_DISCONNECTED");
                end_match(match, (match->fd_giocatore1 == client_socket) ? 1 : 0);
            } 
            reset_match(id_match);
        }
    }
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
    
    char msg[100];
    snprintf(msg, sizeof(msg), "JOIN_REQUEST %d", client_req);
    send_msg(match->fd_giocatore1, msg);
    
    while (match->join_status == 0) 
        pthread_cond_wait(&match->cond_join, &mutex_match); 
    
    int result = (match->join_status == 1) ? 1 : 0;
    
    pthread_mutex_unlock(&mutex_match);
    return result;
}

int handle_msg(int client_socket, int *current_match_id, char *buffer) {
    buffer[strcspn(buffer, "\r\n")] = '\0';
    printf("HANDLING: %s\n", buffer);
    fflush(stdout); 

    int id_match, col, player;

    if (strcmp(buffer, "CREATE") == 0) {
        *current_match_id = create_match(client_socket);
        char msg[100];
        snprintf(msg, sizeof(msg), "THE MATCH %d IS CREATED, JOIN!!", *current_match_id);
        broadcast(msg, client_socket, -1);
        if (*current_match_id != -1) 
            send_msg(client_socket,"WAIT TURN");
        
    }
    else if (sscanf(buffer, "JOIN %d", &id_match) == 1) {
        printf("Joining %d\n", id_match);
        if(request_to_creator(id_match, client_socket)){
            if (join_match_request(id_match, client_socket)) {
                *current_match_id = id_match;
                int fd_creator = get_opponent_fd(id_match, client_socket);
                printf("FD_OPPONENT IN JOIN: %d, FD_JOINER: %d\n", fd_creator, client_socket);
                if (fd_creator != -1) {
                    send_msg(fd_creator, "YOUR TURN");   
                    send_msg(client_socket, "WAIT TURN");
                    char msg[100];
                    snprintf(msg, sizeof(msg), "THE MATCH %d IS STARING", id_match);
                    broadcast(msg, client_socket, fd_creator);
                }
            }else 
                send_msg(client_socket, "ERROR Impossibile unirsi alla partita\n");
            
        }else{
            send_msg(client_socket, "JOIN Rejected\n");
            pthread_mutex_lock(&mutex_match);
            Match *match = get_match_by_Id(id_match);
            if (match != NULL) 
                match->fd_giocatore2 = -1;
            
            pthread_mutex_unlock(&mutex_match);
        }
        
        
    }
    else if (sscanf(buffer, "MOVE %d ", &col) >= 1) {
        
        int id_match = -1;
        int id_opp = get_match_and_opponent(client_socket, &id_match); 
            if (id_opp != -1 && id_match != -1){
                    fflush(stdout);
                    int row = play_turn(id_match, col);
                    pthread_mutex_lock(&mutex_match);
                    Match *match = get_match_by_Id(id_match);
                if(match != NULL){
                    int player_num = (match->fd_giocatore1 == client_socket) ? 1 : 2;
                    char msg[100];
                    snprintf(msg, sizeof(msg), "UPDATE_BOARD %d %d %d", player_num, row, col);
                    send_msg(client_socket, msg);
                    send_msg(id_opp, msg);
                    usleep(1000);
                
                if (check_win(match, col)) {
                    printf("MATCH: %d WINNER: %d\n", id_match, client_socket);
                    end_match(match, (client_socket == match->fd_giocatore1) ? 0 : 1);
                    match->state = status_terminated;
                    match->p1_rematch = 0;
                    match->p2_rematch = 0;
                    pthread_mutex_unlock(&mutex_match);
                    //reset_match(id_match);
                } 
                else if (check_draw(match)) {
                    printf("DRAW\n");
                    end_match(match, 2);
                    match->state = status_terminated;
                    match->p1_rematch = 0;
                    match->p2_rematch = 0;
                    pthread_mutex_unlock(&mutex_match);
                    //reset_match(id_match);
                } 
                else {
                    send_msg(client_socket, "WAIT TURN");
                    send_msg(id_opp, "YOUR TURN");
                    pthread_mutex_unlock(&mutex_match);
                }
            } else{
                pthread_mutex_unlock(&mutex_match);
                printf("Errore: impossibile recuperare la struttura della partita %d\n", id_match);
            }
        
        } else
            printf("ERRORE MOVE\n"); 
    } else if (strncmp(buffer, "QUIT", 4) == 0) {
        id_match = -1;
        int id_opp = get_match_and_opponent(client_socket, &id_match);

        if (id_match != -1) {
            Match *match = get_match_by_Id(id_match);
            if (match != NULL) 
                end_match(match, (match->fd_giocatore1 == client_socket) ? 1 : 0);
            
        }else 
            printf("QUIT: MATCH  %d NOT FOUND\n", id_match);
        
    } else if (strcmp(buffer, "DISCONNECT") == 0) {
        handle_client_exit(client_socket);
        return -1;
    }else if( strcmp(buffer, "ACCEPT") == 0){
        pthread_mutex_lock(&mutex_match);
        Match *match = NULL;
        for (int i = 0; i < MAX_MATCHES; i++) 
            if (matches[i].fd_giocatore1 == client_socket && matches[i].fd_giocatore2 != -1 && matches[i].join_status == 0) {
                match = &matches[i];
                break;
            }
        
        
        if (match != NULL) {
            match->join_status = 1; 
            pthread_cond_signal(&match->cond_join);
        }
        
        pthread_mutex_unlock(&mutex_match);
    }else if( strcmp(buffer, "REJECT") == 0){
        pthread_mutex_lock(&mutex_match);
        
        Match *match = NULL;
        for (int i = 0; i < MAX_MATCHES; i++) 
            if (matches[i].fd_giocatore1 == client_socket && matches[i].fd_giocatore2 != -1 && matches[i].join_status == 0) {
                match = &matches[i];
                break;
            }
        
        
        if (match != NULL) {
            match->join_status = 2;
            pthread_cond_signal(&match->cond_join);
        }
        
        pthread_mutex_unlock(&mutex_match);
    }else if (strcmp(buffer, "REMATCH_ACCEPT") == 0) {
        pthread_mutex_lock(&mutex_match);
        int match_idx = -1;
        int opp = -1;
        for (int i = 0; i < MAX_MATCHES; i++) {
            if (matches[i].id_match != -1) {
                if (matches[i].fd_giocatore1 == client_socket) {
                    match_idx = i;
                    opp = matches[i].fd_giocatore2;
                    break;
                } else if (matches[i].fd_giocatore2 == client_socket) {
                    match_idx = i;
                    opp = matches[i].fd_giocatore1;
                    break;
                }
            }
        }
        if (match_idx != -1) {
            Match *match = &matches[match_idx];

            if (match->state == status_terminated) {
                if (client_socket == match->fd_giocatore1)
                    match->p1_rematch = 1;
                else
                    match->p2_rematch = 1;
                
                if (match->p1_rematch == 1 && match->p2_rematch == 1) {
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
                }else if (opp != -1) 
                    send_msg(opp, "OPPONENT_WANTS_REMATCH");
                    
              }
            }
            pthread_mutex_unlock(&mutex_match);
        }else if (strcmp(buffer, "REMATCH_DECLINE") == 0) {
            pthread_mutex_lock(&mutex_match);
            int match_idx = -1;
            int opp = -1;
            int id_match = -1;

            for (int i = 0; i < MAX_MATCHES; i++) 
                if (matches[i].id_match != -1) 
                    if (matches[i].fd_giocatore1 == client_socket) {
                        match_idx = i;
                        opp = matches[i].fd_giocatore2;
                        id_match = matches[i].id_match;
                        break;
                    } else if (matches[i].fd_giocatore2 == client_socket) {
                        match_idx = i;
                        opp = matches[i].fd_giocatore1;
                        id_match = matches[i].id_match;
                        break;
                    }

            if (match_idx != -1 && opp != -1 ) 
                send_msg(opp, "REMATCH_DECLINED");
            
    
            pthread_mutex_unlock(&mutex_match);
                    
            if (match_idx != -1)
                reset_match(id_match); 
        }else
            printf("%s\n",buffer);

    return 0;
}
