#include "../../game/connectFour.h"


int handle_quit(int client_socket){
    //rimuovere il giocatore dalla partita e terminare la partita
}
int handle_msg(int client_socket, char * buffer){
    //gestire se è creazione partita, eliminazione partita, unisciti in partita 
    //e mossa in partita
}

int create_match(int fd_creator){}
int join_match_request(int match_id, int fd_applicant){}
void accept_or_reject_player(int match_id, int decision){}
void play_turn(int match_id, int column){}
void end_match(int match_id, int result){}
void reset_match(int match_id){}
//void broadcast_status(){}