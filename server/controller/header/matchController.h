#ifndef MATCHCONTROLLER_H
#define MATCHCONTROLLER_H

int init_matchController();
int get_match_and_opponent(int current_client_fd, int *out_match_id);
int handle_msg(int client_socket, char * buffer);
int create_match(int fd_creator);
int join_match_request(int match_id, int fd_applicant);
void play_turn(int match_id, int column);
void end_match(int match_id, int result);
void reset_match(int match_id);
int handle_quit(int client_socket);
void remove_player_match(int id_player);
void handle_client_exit(int client_socket);

#endif