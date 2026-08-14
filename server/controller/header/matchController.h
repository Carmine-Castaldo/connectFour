#ifndef MATCHCONTROLLER_H
#define MATCHCONTROLLER_H

typedef struct Match Match;

int init_matchController();
void init_match(Match * match, int id_match, int fd_creator);
int create_match(int fd_creator);
int join_match_request(int match_id, int fd_applicant);
int request_to_creator(int id_match, int client_socket);
int play_turn(Match * match, int column);
void end_match(Match * match_id, int result);
void reset_match(int match_id);
void restart_match(Match * match);
void remove_player_match(int id_player);
int get_opponent(int client_socket);
int handle_msg(int client_socket, char * buffer);
void handle_client_disconnect(int client_socket);
void handle_join(int client_socket, int id_match);
void handle_create(int client_socket);
void handle_move(int client_socket, int col);
void handle_quit(int client_socket);
void handle_accept(int client_socket);
void handle_reject(int client_socket);
void handle_rematch_accept(int client_socket);
void handle_rematch_declined(int client_socket);
#endif