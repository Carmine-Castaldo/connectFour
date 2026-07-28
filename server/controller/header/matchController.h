#ifndef MATCHCONTROLLER_H
#define MATCHCONTROLLER_H

int create_match(int fd_creator);
int join_match_request(int match_id, int fd_applicant);
void accept_or_reject_player(int match_id, int decision);
void play_turn(int match_id, int column);
void end_match(int match_id, int result);
void reset_match(int match_id);
//void broadcast_status(){}

#endif